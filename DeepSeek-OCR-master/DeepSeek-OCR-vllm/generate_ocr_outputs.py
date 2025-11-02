import threading
import queue
import os
import pickle
import argparse
import re
import io
import logging
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import torch
from config import MODEL_PATH, OUTPUT_PATH, PROMPT, SKIP_REPEAT, MAX_CONCURRENCY, CROP_MODE
from deepseek_ocr import DeepseekOCRForCausalLM
from vllm.model_executor.models.registry import ModelRegistry
from vllm import LLM, SamplingParams
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor

# Setup logger
logger = logging.getLogger("generate_ocr")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("generate_ocr.log")
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(fh)


# Set environment variables
if torch.version.cuda == '11.8':
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda-11.8/bin/ptxas"
os.environ['VLLM_USE_V1'] = '0'
os.environ["CUDA_VISIBLE_DEVICES"] = '0'


def load_batch_background(file_batch, batch_queue, batch_idx):
    """Load a batch of pickle files in the background"""
    try:
        logger.info(f"Background loading batch {batch_idx}: {len(file_batch)} files")

        batch_tokenized_data = []
        pdf_info = []

        for pickle_file in file_batch:
            logger.debug(f"Loading {pickle_file}")
            try:
                with open(pickle_file, 'rb') as f:
                    data = pickle.load(f)

                # Handle individual PDF format
                if 'tokenized_data' in data and 'image_paths' in data:
                    pdf_name = os.path.splitext(os.path.basename(pickle_file))[0]
                    if pdf_name.endswith('.pdf'):
                        pdf_name = pdf_name[:-4]
                    num_items = len(data['tokenized_data'])
                    num_images = len(data['image_paths'])

                    batch_tokenized_data.extend(data['tokenized_data'])

                    # Track PDF info for splitting results later
                    pdf_info.append({
                        'name': pdf_name,
                        'num_items': num_items,
                        'num_images': num_images,
                        'image_paths': data['image_paths'],
                        'metadata': data
                    })
                else:
                    logger.warning(f"Unexpected pickle file format in {pickle_file}")

            except Exception as e:
                logger.error(f"Error loading {pickle_file}: {e}")
                continue

        batch_data = {
            'tokenized_data': batch_tokenized_data,
            'pdf_info': pdf_info,
            'batch_idx': batch_idx
        }

        batch_queue.put(batch_data)
        logger.info(f"Background loading completed for batch {batch_idx}: {len(batch_tokenized_data)} items from {len(pdf_info)} PDFs")

    except Exception as e:
        logger.error(f"Background loading failed for batch {batch_idx}: {e}")
        batch_queue.put(None)  # Signal failure


def load_all_tokenized_data(tokenized_dir):
    """Load all tokenized data from directory with saved images"""
    logger.info(f"Loading all tokenized data from {tokenized_dir}")

    # Look for both batch files and individual PDF files
    all_pickle_files = [os.path.join(tokenized_dir, f) for f in os.listdir(tokenized_dir)
                       if f.endswith('.pkl')]
    all_pickle_files.sort()

    all_tokenized_data = []
    all_metadata = []
    all_images = []

    for pickle_file in all_pickle_files:
        logger.debug(f"Loading {pickle_file}")
        try:
            with open(pickle_file, 'rb') as f:
                data = pickle.load(f)

            # Handle both batch format and individual PDF format
            if 'tokenized_data' in data and 'metadata' in data and 'image_paths' in data:
                # This is batch format or individual PDF format
                all_tokenized_data.extend(data['tokenized_data'])
                all_metadata.extend(data['metadata']) if isinstance(data['metadata'], list) else all_metadata.append(data['metadata'])

                # Load images for this file
                for image_path in data['image_paths']:
                    if os.path.exists(image_path):
                        img = Image.open(image_path)
                        all_images.append(img)
                    else:
                        logger.warning(f"Saved image not found: {image_path}")
            else:
                logger.warning(f"Unexpected pickle file format in {pickle_file}")

        except Exception as e:
            logger.error(f"Error loading {pickle_file}: {e}")
            continue

    logger.info(f"Loaded {len(all_tokenized_data)} tokenized items and {len(all_images)} images")
    return all_tokenized_data, all_metadata, all_images


def load_single_tokenized_pdf(tokenized_file):
    """Load tokenized data for a single PDF with saved images"""
    logger.debug(f"Loading tokenized data from {tokenized_file}")
    with open(tokenized_file, 'rb') as f:
        data = pickle.load(f)

    # Load images from saved paths
    original_images = []
    for image_path in data['image_paths']:
        if os.path.exists(image_path):
            img = Image.open(image_path)
            original_images.append(img)
        else:
            raise FileNotFoundError(f"Saved image not found: {image_path}")

    logger.debug(f"Loaded {len(original_images)} images from {tokenized_file}")
    return data['tokenized_data'], data, original_images


def re_match(text):
    pattern = r'(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)'
    matches = re.findall(pattern, text, re.DOTALL)

    mathes_image = []
    mathes_other = []
    for a_match in matches:
        if '<|ref|>image<|/ref|>' in a_match[0]:
            mathes_image.append(a_match[0])
        else:
            mathes_other.append(a_match[0])
    return matches, mathes_image, mathes_other


def extract_coordinates_and_label(ref_text, image_width, image_height):
    try:
        label_type = ref_text[1]
        cor_list = eval(ref_text[2])
    except Exception as e:
        print(e)
        return None
    return (label_type, cor_list)


def draw_bounding_boxes(image, refs, jdx, output_path):
    image_width, image_height = image.size
    img_draw = image.copy()
    draw = ImageDraw.Draw(img_draw)

    overlay = Image.new('RGBA', img_draw.size, (0, 0, 0, 0))
    draw2 = ImageDraw.Draw(overlay)

    font = ImageFont.load_default()

    img_idx = 0

    for i, ref in enumerate(refs):
        try:
            result = extract_coordinates_and_label(ref, image_width, image_height)
            if result:
                label_type, points_list = result

                color = (np.random.randint(0, 200), np.random.randint(0, 200), np.random.randint(0, 255))
                color_a = color + (20, )

                for points in points_list:
                    x1, y1, x2, y2 = points

                    x1 = int(x1 / 999 * image_width)
                    y1 = int(y1 / 999 * image_height)
                    x2 = int(x2 / 999 * image_width)
                    y2 = int(y2 / 999 * image_height)

                    if label_type == 'image':
                        try:
                            cropped = image.crop((x1, y1, x2, y2))
                            cropped.save(f"{output_path}/images/{jdx}_{img_idx}.jpg")
                        except Exception as e:
                            print(e)
                            pass
                        img_idx += 1

                    try:
                        if label_type == 'title':
                            draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
                            draw2.rectangle([x1, y1, x2, y2], fill=color_a, outline=(0, 0, 0, 0), width=1)
                        else:
                            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                            draw2.rectangle([x1, y1, x2, y2], fill=color_a, outline=(0, 0, 0, 0), width=1)

                        text_x = x1
                        text_y = max(0, y1 - 15)

                        text_bbox = draw.textbbox((0, 0), label_type, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_height = text_bbox[3] - text_bbox[1]
                        draw.rectangle([text_x, text_y, text_x + text_width, text_y + text_height],
                                    fill=(255, 255, 255, 30))

                        draw.text((text_x, text_y), label_type, font=font, fill=color)
                    except:
                        pass
        except:
            continue
    img_draw.paste(overlay, (0, 0), overlay)
    return img_draw


def process_image_with_refs(image, ref_texts, jdx, output_path):
    result_image = draw_bounding_boxes(image, ref_texts, jdx, output_path)
    return result_image


def pil_to_pdf_img2pdf(pil_images, output_path):
    import img2pdf

    if not pil_images:
        return

    image_bytes_list = []

    for img in pil_images:
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=95)
        img_bytes = img_buffer.getvalue()
        image_bytes_list.append(img_bytes)

    try:
        pdf_bytes = img2pdf.convert(image_bytes_list)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
    except Exception as e:
        print(f"error: {e}")


def save_pdf_results(outputs_list, metadata, original_images, output_path):
    """Save OCR results for a single PDF"""

    logger.debug(f"Saving results for {len(outputs_list)} pages to {output_path}")

    # Process results
    mmd_det_path = os.path.join(output_path, 'ocr_detailed.mmd')
    mmd_path = os.path.join(output_path, 'ocr_content.mmd')
    pdf_out_path = os.path.join(output_path, 'ocr_layout.pdf')

    contents_det = ''
    contents = ''
    draw_images = []
    jdx = 0

    for output, img in zip(outputs_list, original_images):
        content = output.outputs[0].text

        if '<｜end▁of▁sentence｜>' in content:
            content = content.replace('<｜end▁of▁sentence｜>', '')
        else:
            if SKIP_REPEAT:
                continue

        page_num = f'\n<--- Page {jdx + 1} --->'
        contents_det += content + f'\n{page_num}\n'

        image_draw = img.copy()
        matches_ref, matches_images, mathes_other = re_match(content)
        result_image = process_image_with_refs(image_draw, matches_ref, jdx, output_path)

        draw_images.append(result_image)

        for idx, a_match_image in enumerate(matches_images):
            content = content.replace(a_match_image, f'![](images/' + str(jdx) + '_' + str(idx) + '.jpg)\n')

        for idx, a_match_other in enumerate(mathes_other):
            content = content.replace(a_match_other, '').replace('\\coloneqq', ':=').replace('\\eqqcolon', '=:').replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')

        contents += content + f'\n{page_num}\n'
        jdx += 1

    # Save outputs
    logger.debug("Saving output files")
    with open(mmd_det_path, 'w', encoding='utf-8') as afile:
        afile.write(contents_det)

    with open(mmd_path, 'w', encoding='utf-8') as afile:
        afile.write(contents)

    pil_to_pdf_img2pdf(draw_images, pdf_out_path)

    logger.debug(f"Saved PDF results to {output_path}")


def generate_ocr_outputs(tokenized_data, metadata, original_images, output_path, llm, sampling_params):
    """Generate OCR outputs from tokenized data"""

    logger.info(f"Starting OCR generation for {len(tokenized_data)} items to {output_path}")

    os.makedirs(output_path, exist_ok=True)
    os.makedirs(f'{output_path}/images', exist_ok=True)

    # Generate outputs in batches
    logger.debug("Starting VLLM generation")
    outputs_list = llm.generate(tokenized_data, sampling_params=sampling_params)

    # Process results
    mmd_det_path = os.path.join(output_path, 'combined_det.mmd')
    mmd_path = os.path.join(output_path, 'combined.mmd')
    pdf_out_path = os.path.join(output_path, 'combined_layouts.pdf')

    contents_det = ''
    contents = ''
    draw_images = []
    jdx = 0

    logger.debug("Processing generation results")
    for output, img in tqdm(zip(outputs_list, original_images), desc="Processing OCR results", unit="page", total=len(outputs_list), ncols=80):
        content = output.outputs[0].text

        if '<｜end▁of▁sentence｜>' in content:
            content = content.replace('<｜end▁of▁sentence｜>', '')
        else:
            if SKIP_REPEAT:
                continue

        page_num = f'\n<--- Page Split --->'
        contents_det += content + f'\n{page_num}\n'

        image_draw = img.copy()
        matches_ref, matches_images, mathes_other = re_match(content)
        result_image = process_image_with_refs(image_draw, matches_ref, jdx, output_path)

        draw_images.append(result_image)

        for idx, a_match_image in enumerate(matches_images):
            content = content.replace(a_match_image, f'![](images/' + str(jdx) + '_' + str(idx) + '.jpg)\n')

        for idx, a_match_other in enumerate(mathes_other):
            content = content.replace(a_match_other, '').replace('\\coloneqq', ':=').replace('\\eqqcolon', '=:').replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')

        contents += content + f'\n{page_num}\n'
        jdx += 1

    # Save outputs
    logger.debug("Saving output files")
    with open(mmd_det_path, 'w', encoding='utf-8') as afile:
        afile.write(contents_det)

    with open(mmd_path, 'w', encoding='utf-8') as afile:
        afile.write(contents)

    pil_to_pdf_img2pdf(draw_images, pdf_out_path)

    logger.info(f"Generated outputs saved to {output_path}")
    print(f"Generated outputs saved to {output_path}")


def main():
    logger.info("Starting OCR generation process")

    parser = argparse.ArgumentParser(description="Generate OCR outputs from tokenized data")
    parser.add_argument("--tokenized-dir", "-t", help="Directory containing tokenized data batches")
    parser.add_argument("--tokenized-file", "-f", help="Single tokenized data file")
    parser.add_argument("--original-pdfs", "-p", help="Directory containing original PDF files")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--batch-size", "-b", type=int, default=50, help="Number of pickle files to load per VLLM batch (each PDF gets its own output directory)")

    args = parser.parse_args()

    logger.info(f"Arguments: tokenized_dir={args.tokenized_dir}, tokenized_file={args.tokenized_file}, output={args.output}, batch_size={args.batch_size}")

    # Initialize VLLM model
    logger.debug("Initializing VLLM model")
    ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

    llm = LLM(
        model=MODEL_PATH,
        hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
        block_size=256,
        enforce_eager=False,
        trust_remote_code=True,
        max_model_len=8192,
        swap_space=0,
        max_num_seqs=MAX_CONCURRENCY,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.9,
        disable_mm_preprocessor_cache=True,
        dtype='bfloat16'
    )

    logits_processors = [NoRepeatNGramLogitsProcessor(ngram_size=20, window_size=50, whitelist_token_ids={128821, 128822})]
    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=8192,
        logits_processors=logits_processors,
        skip_special_tokens=False,
        include_stop_str_in_output=True,
    )

    # Load and process tokenized data in batches
    logger.debug("Starting batch processing of tokenized data")

    if args.tokenized_file:
        # Single file processing
        tokenized_data, metadata, original_images = load_single_tokenized_pdf(args.tokenized_file)
        logger.info(f"Loaded {len(tokenized_data)} tokenized items and {len(original_images)} images")

        # Process single file
        pdf_name = os.path.splitext(os.path.basename(args.tokenized_file))[0]
        # Remove .pdf extension if present for cleaner folder names
        if pdf_name.endswith('.pdf'):
            pdf_name = pdf_name[:-4]
        pdf_output_dir = os.path.join(args.output, pdf_name)
        os.makedirs(pdf_output_dir, exist_ok=True)
        os.makedirs(f'{pdf_output_dir}/images', exist_ok=True)

        # Generate outputs
        logger.debug("Starting VLLM generation")
        outputs_list = llm.generate(tokenized_data, sampling_params=sampling_params)

        # Save results
        save_pdf_results(outputs_list, metadata, original_images, pdf_output_dir)
    else:
        # Directory processing - load pickle files in batches and process each batch through VLLM
        all_pickle_files = [os.path.join(args.tokenized_dir, f) for f in os.listdir(args.tokenized_dir)
                           if f.endswith('.pkl')]
        all_pickle_files.sort()

        logger.info(f"Found {len(all_pickle_files)} pickle files to process in batches")

        # Process files in batches with background loading
        file_batch_size = args.batch_size  # Number of pickle files to load per batch
        total_file_batches = (len(all_pickle_files) + file_batch_size - 1) // file_batch_size
        batch_queue = queue.Queue(maxsize=2)  # Buffer up to 2 batches

        # Start background loading for first batch
        current_batch_idx = 0
        if current_batch_idx < total_file_batches:
            file_batch_start = current_batch_idx * file_batch_size
            file_batch_end = min((current_batch_idx + 1) * file_batch_size, len(all_pickle_files))
            first_batch = all_pickle_files[file_batch_start:file_batch_end]
            background_thread = threading.Thread(
                target=load_batch_background,
                args=(first_batch, batch_queue, current_batch_idx + 1)
            )
            background_thread.start()
            current_batch_idx += 1

        # Process batches with overlapping I/O and computation
        processed_batches = 0
        while processed_batches < total_file_batches:
            # Wait for current batch to be loaded
            try:
                batch_data = batch_queue.get(timeout=300)  # 5 minute timeout
                if batch_data is None:
                    logger.error("Batch loading failed, skipping")
                    break
            except queue.Empty:
                logger.error("Timeout waiting for batch to load")
                break

            batch_tokenized_data = batch_data['tokenized_data']
            pdf_info = batch_data['pdf_info']
            batch_idx = batch_data['batch_idx']

            logger.info(f"Processing batch {batch_idx}/{total_file_batches}: {len(batch_tokenized_data)} items from {len(pdf_info)} PDFs")

            if not batch_tokenized_data:
                logger.warning(f"No valid data in batch {batch_idx}, skipping")
                # Start loading next batch if available
                if current_batch_idx < total_file_batches:
                    file_batch_start = current_batch_idx * file_batch_size
                    file_batch_end = min((current_batch_idx + 1) * file_batch_size, len(all_pickle_files))
                    next_batch = all_pickle_files[file_batch_start:file_batch_end]
                    background_thread = threading.Thread(
                        target=load_batch_background,
                        args=(next_batch, batch_queue, current_batch_idx + 1)
                    )
                    background_thread.start()
                    current_batch_idx += 1
                continue

            # Start background loading for next batch while processing current
            if current_batch_idx < total_file_batches:
                file_batch_start = current_batch_idx * file_batch_size
                file_batch_end = min((current_batch_idx + 1) * file_batch_size, len(all_pickle_files))
                next_batch = all_pickle_files[file_batch_start:file_batch_end]
                background_thread = threading.Thread(
                    target=load_batch_background,
                    args=(next_batch, batch_queue, current_batch_idx + 1)
                )
                background_thread.start()
                current_batch_idx += 1

            # Process this batch through VLLM
            logger.debug("Starting VLLM generation")
            outputs_list = llm.generate(batch_tokenized_data, sampling_params=sampling_params)

            # Split results back by PDF and save each PDF separately
            item_offset = 0

            for pdf_data in pdf_info:
                pdf_name = pdf_data['name']
                num_items = pdf_data['num_items']
                image_paths = pdf_data['image_paths']
                pdf_metadata = pdf_data['metadata']

                # Extract this PDF's results from the batch
                pdf_outputs = outputs_list[item_offset:item_offset + num_items]

                # Load images for this PDF on-demand (in parallel for speed)
                from concurrent.futures import ThreadPoolExecutor
                def load_image(image_path):
                    if os.path.exists(image_path):
                        return Image.open(image_path)
                    else:
                        logger.warning(f"Saved image not found: {image_path}")
                        return None

                with ThreadPoolExecutor(max_workers=min(8, len(image_paths))) as executor:
                    pdf_images = list(executor.map(load_image, image_paths))
                pdf_images = [img for img in pdf_images if img is not None]  # Filter out None values

                # Create PDF-specific output directory
                pdf_output_dir = os.path.join(args.output, pdf_name)
                os.makedirs(pdf_output_dir, exist_ok=True)
                os.makedirs(f'{pdf_output_dir}/images', exist_ok=True)

                logger.info(f"Saving results for PDF: {pdf_name} to {pdf_output_dir}")

                # Process and save this PDF's results
                save_pdf_results(pdf_outputs, pdf_metadata, pdf_images, pdf_output_dir)

                item_offset += num_items

            processed_batches += 1

    logger.info("OCR generation process completed")


if __name__ == "__main__":
    main()