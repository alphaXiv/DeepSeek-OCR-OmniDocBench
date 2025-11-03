import os
import fitz
import io
import pickle
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, cpu_count
from PIL import Image
import torch
import logging
from config import NUM_WORKERS, CROP_MODE
from process.image_process import DeepseekOCRProcessor

# Setup logger
logger = logging.getLogger("tokenize_ocr")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("tokenize_ocr.log")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(fh)


def pdf_to_images_high_quality(pdf_path, dpi=144, image_format="PNG"):
    """
    Convert PDF to high quality images
    """
    images = []

    pdf_document = fitz.open(pdf_path)

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]

        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        Image.MAX_IMAGE_PIXELS = None

        if image_format.upper() == "PNG":
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
        else:
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

        images.append(img)

    pdf_document.close()
    return images


def process_single_image(image):
    """Tokenize a single image"""
    from config import PROMPT
    prompt_in = PROMPT
    cache_item = {
        "prompt": prompt_in,
        "multi_modal_data": {"image": DeepseekOCRProcessor().tokenize_with_images(images=[image], bos=True, eos=True, cropping=CROP_MODE)},
    }
    return cache_item


def process_single_pdf(pdf_path, output_dir):
    """
    Process a single PDF: convert to images, save them, tokenize, and save results
    This function saves individual pickle files for multiprocessing compatibility
    """
    try:
        logger.debug(f"Converting PDF to images: {pdf_path}")
        # Convert PDF to images
        images = pdf_to_images_high_quality(pdf_path)

        # Create PDF-specific image directory
        pdf_name = os.path.basename(pdf_path).replace('.pdf', '')
        images_base_dir = os.path.join(output_dir, 'images')
        pdf_images_dir = os.path.join(images_base_dir, pdf_name)
        os.makedirs(pdf_images_dir, exist_ok=True)

        # Save images and collect paths
        pdf_image_paths = []
        for page_idx, image in enumerate(images):
            image_filename = f"page_{page_idx:03d}.png"
            image_path = os.path.join(pdf_images_dir, image_filename)
            image.save(image_path, 'PNG')
            pdf_image_paths.append(image_path)

        logger.debug(f"Saved {len(pdf_image_paths)} images for {pdf_name} in {pdf_images_dir}")

        # Tokenize all images in this PDF using threading (safe within multiprocessing workers)
        with ThreadPoolExecutor(max_workers=min(cpu_count(), len(images))) as executor:
            pdf_tokenized = list(tqdm(
                executor.map(process_single_image, images),
                desc=f"Tokenizing {pdf_name}",
                unit="page",
                total=len(images),
                ncols=80
            ))

        # Create metadata
        metadata = {
            'pdf_path': pdf_path,
            'pdf_name': pdf_name,
            'num_pages': len(images),
            'tokenized_count': len(pdf_tokenized),
            'image_paths': pdf_image_paths,
            'images_dir': pdf_images_dir
        }

        # Save individual pickle file for this PDF
        output_file = os.path.join(output_dir, f"{pdf_name}_tokenized.pkl")
        with open(output_file, 'wb') as f:
            pickle.dump({
                'pdf_path': pdf_path,
                'pdf_name': pdf_name,
                'num_pages': len(images),
                'tokenized_data': pdf_tokenized,
                'image_paths': pdf_image_paths,
                'images_dir': pdf_images_dir
            }, f)

        logger.info(f"Saved tokenized data to {output_file} ({len(pdf_tokenized)} pages, {len(pdf_image_paths)} images)")
        return True  # Success

    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")
        return False


def tokenize_pdf_batch(pdf_paths, output_dir, batch_size=100, num_workers=None):
    """
    Tokenize a batch of PDFs and save tokenized data with images using multiprocessing
    Find and process only PDFs that haven't been tokenized yet
    """
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    if num_workers is None:
        num_workers = min(cpu_count(), 4)  # Default to 4 workers max to avoid memory issues

    logger.info(f"Starting batch tokenization with batch_size={batch_size}, num_workers={num_workers}")

    # Filter out PDFs that have already been processed (check if tokenized file exists)
    unprocessed_pdf_paths = []

    for pdf_path in pdf_paths:
        pdf_name = os.path.basename(pdf_path).replace('.pdf', '')
        tokenized_file = os.path.join(output_dir, f"{pdf_name}_tokenized.pkl")

        if os.path.exists(tokenized_file):
            logger.debug(f"Skipping already processed PDF: {pdf_name}")
        else:
            unprocessed_pdf_paths.append(pdf_path)

    logger.info(f"Found {len(pdf_paths)} total PDFs, {len(unprocessed_pdf_paths)} unprocessed PDFs to tokenize")

    if not unprocessed_pdf_paths:
        logger.info("All PDFs have already been processed. Nothing to do.")
        return

    # Overall progress bar for all PDFs
    overall_progress = tqdm(
        total=len(unprocessed_pdf_paths),
        desc="Overall Progress",
        unit="PDF",
        ncols=100,
        position=0
    )

    # Process unprocessed PDFs in batches
    for batch_start in range(0, len(unprocessed_pdf_paths), batch_size):
        batch_end = min(batch_start + batch_size, len(unprocessed_pdf_paths))
        batch_paths = unprocessed_pdf_paths[batch_start:batch_end]

        # Calculate batch number for logging (1-indexed)
        batch_num = (batch_start // batch_size) + 1

        logger.info(f"Processing batch {batch_num}: {len(batch_paths)} PDFs using {num_workers} workers")

        # Process PDFs in parallel - each worker saves its own file
        # Create argument tuples for starmap: (pdf_path, output_dir)
        pdf_args = [(pdf_path, output_dir) for pdf_path in batch_paths]

        with Pool(processes=num_workers) as pool:
            # Use starmap to pass multiple arguments
            results = list(tqdm(
                pool.starmap(process_single_pdf, pdf_args),
                desc=f"Batch {batch_num}",
                unit="PDF",
                total=len(batch_paths),
                ncols=80,
                position=1,
                leave=False
            ))

        # Count successful processing and update overall progress
        successful_count = sum(1 for result in results if result)
        overall_progress.update(successful_count)
        logger.info(f"Successfully processed {successful_count}/{len(batch_paths)} PDFs in batch {batch_num}")

        # Note: Individual pickle files are saved by each worker process
        # No batch file needed since generation loads all individual files

    overall_progress.close()
    logger.info("Batch tokenization completed")


def tokenize_single_pdf(pdf_path, output_dir):
    """
    Tokenize a single PDF and save tokenized data with images
    """
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    logger.info(f"Starting tokenization of single PDF: {pdf_path}")

    try:
        logger.debug(f"Converting PDF to images: {pdf_path}")
        # Convert PDF to images
        images = pdf_to_images_high_quality(pdf_path)

        # Create PDF-specific image directory
        pdf_name = os.path.basename(pdf_path).replace('.pdf', '')
        pdf_images_dir = os.path.join(images_dir, pdf_name)
        os.makedirs(pdf_images_dir, exist_ok=True)

        # Save images and collect paths
        image_paths = []

        for page_idx, image in enumerate(images):
            image_filename = f"page_{page_idx:03d}.png"
            image_path = os.path.join(pdf_images_dir, image_filename)
            image.save(image_path, 'PNG')
            image_paths.append(image_path)

        logger.debug(f"Saved {len(image_paths)} images for {pdf_name} in {pdf_images_dir}")

        # Tokenize all images using threading
        with ThreadPoolExecutor(max_workers=min(cpu_count(), len(images))) as executor:
            tokenized_data = list(tqdm(
                executor.map(process_single_image, images),
                desc=f"Tokenizing {pdf_name}",
                unit="page",
                total=len(images),
                ncols=80
            ))

        # Save tokenized data
        output_file = os.path.join(output_dir, f"{pdf_name}_tokenized.pkl")

        with open(output_file, 'wb') as f:
            pickle.dump({
                'pdf_path': pdf_path,
                'pdf_name': pdf_name,
                'num_pages': len(images),
                'tokenized_data': tokenized_data,
                'image_paths': image_paths,
                'images_dir': pdf_images_dir
            }, f)

        logger.info(f"Saved tokenized data to {output_file} ({len(tokenized_data)} pages, {len(image_paths)} images)")

    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tokenize OCR data for batch processing")
    parser.add_argument("--input", "-i", required=True, help="Input PDF file or directory")
    parser.add_argument("--output", "-o", required=True, help="Output directory for tokenized data")
    parser.add_argument("--batch-size", "-b", type=int, default=50, help="Batch size for processing multiple PDFs")
    parser.add_argument("--workers", "-w", type=int, default=None, help="Number of worker processes (default: min(cpu_count, 4))")
    parser.add_argument("--single", "-s", action="store_true", help="Process single PDF instead of batch")

    args = parser.parse_args()

    logger.info(f"Starting tokenization with args: input={args.input}, output={args.output}, batch_size={args.batch_size}, workers={args.workers}, single={args.single}")

    if args.single:
        tokenize_single_pdf(args.input, args.output)
    else:
        if os.path.isfile(args.input):
            pdf_paths = [args.input]
        else:
            pdf_paths = [os.path.join(args.input, f) for f in os.listdir(args.input)
                        if f.lower().endswith('.pdf')]

        logger.info(f"Found {len(pdf_paths)} PDF files to process")
        tokenize_pdf_batch(pdf_paths, args.output, args.batch_size, args.workers)

    logger.info("Tokenization completed")