import os
import json
import sys
from tqdm import tqdm
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Copied from run_dpsk_ocr_image.py for VLLM initialization
import asyncio
import re
import torch
if torch.version.cuda == '11.8':
    os.environ["TRITON_PTXAS_PATH"] = "/usr/local/cuda-11.8/bin/ptxas"

os.environ['VLLM_USE_V1'] = '0'
os.environ["CUDA_VISIBLE_DEVICES"] = '0'

from vllm import LLM, SamplingParams
from vllm.model_executor.models.registry import ModelRegistry
import time
from deepseek_ocr import DeepseekOCRForCausalLM
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor
from config import MODEL_PATH, INPUT_PATH, OUTPUT_PATH, PROMPT, SKIP_REPEAT, MAX_CONCURRENCY, NUM_WORKERS, CROP_MODE

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from deepseek_ocr import DeepseekOCRForCausalLM

from vllm.model_executor.models.registry import ModelRegistry

from vllm import LLM, SamplingParams
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor

# Additional imports for PDF processing
import fitz
import img2pdf
import io
from concurrent.futures import ThreadPoolExecutor

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

logits_processors = [NoRepeatNGramLogitsProcessor(ngram_size=20, window_size=50, whitelist_token_ids= {128821, 128822})] #window for fast；whitelist_token_ids: <td>,</td>

sampling_params = SamplingParams(
    temperature=0.0,
    max_tokens=8192,
    logits_processors=logits_processors,
    skip_special_tokens=False,
    include_stop_str_in_output=True,
)

def pdf_to_images_high_quality(pdf_path, dpi=144, image_format="PNG"):
    """
    pdf2images
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

def pil_to_pdf_img2pdf(pil_images, output_path):

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
    
    #     except IOError:
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


def process_single_image(image):
    """single image"""
    prompt_in = PROMPT
    cache_item = {
        "prompt": prompt_in,
        "multi_modal_data": {"image": DeepseekOCRProcessor().tokenize_with_images(images = [image], bos=True, eos=True, cropping=CROP_MODE)},
    }
    return cache_item


def process_pdf_batch_to_ocr(pdf_batch, output_base_dir, max_images_per_batch=1000):
    """
    Process multiple PDFs in batched llm.generate() calls for better GPU utilization.
    Never splits a single PDF across multiple batches - processes large PDFs individually.

    Args:
        pdf_batch: List of (pdf_filename, pdf_path) tuples
        output_base_dir: Base directory for outputs
        max_images_per_batch: Maximum images to process in one batch to prevent OOM
    """
    # Separate large PDFs from small ones
    large_pdfs = []
    small_pdfs = []
    current_batch = []
    current_batch_images = 0

    for pdf_filename, pdf_path in pdf_batch:
        paper_id = os.path.splitext(pdf_filename)[0]
        output_dir = os.path.join(output_base_dir, paper_id)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f'{output_dir}/images', exist_ok=True)

        print(f'Loading PDF: {pdf_filename}')
        images = pdf_to_images_high_quality(pdf_path)

        if len(images) > max_images_per_batch:
            # This PDF is too large for batching - process individually
            large_pdfs.append((pdf_filename, pdf_path, images, output_dir))
        else:
            # Check if adding this PDF would exceed batch limit
            if current_batch_images + len(images) > max_images_per_batch and current_batch:
                # Yield current batch
                yield current_batch
                current_batch = []
                current_batch_images = 0

            # Add to current batch
            current_batch.append((pdf_filename, pdf_path, images, output_dir))
            current_batch_images += len(images)

    # Yield remaining batch
    if current_batch:
        yield current_batch

    # Yield large PDFs as individual batches
    for large_pdf in large_pdfs:
        yield [large_pdf]


def process_batched_pdfs(pdf_batch, output_base_dir, max_images_per_batch=1000):
    """
    Process a batch of PDFs using batched LLM inference.
    """
    total_success = 0
    total_failed = 0
    
    for batch in process_pdf_batch_to_ocr(pdf_batch, output_base_dir, max_images_per_batch):
        if not batch:
            continue

        # Collect all images from this batch
        all_images = []
        pdf_info_list = []

        for pdf_filename, pdf_path, images, output_dir in batch:
            start_idx = len(all_images)
            end_idx = start_idx + len(images)

            pdf_info_list.append({
                'filename': pdf_filename,
                'path': pdf_path,
                'output_dir': output_dir,
                'images': images,
                'image_start_idx': start_idx,
                'image_end_idx': end_idx
            })

            all_images.extend(images)

        print(f'Processing batch of {len(all_images)} images from {len(batch)} PDFs')

        # Pre-process all images in parallel
        NUM_WORKERS = os.cpu_count()
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            batch_inputs = list(tqdm(
                executor.map(process_single_image, all_images),
                total=len(all_images),
                desc="Pre-processing images"
            ))

        # Single batched LLM call for all images
        outputs_list = llm.generate(batch_inputs, sampling_params=sampling_params)

        # Process outputs per PDF
        image_idx = 0
        for pdf_info in pdf_info_list:
            try:
                pdf_images = pdf_info['images']
                pdf_output_dir = pdf_info['output_dir']
                pdf_filename = pdf_info['filename']
                pdf_path = pdf_info['path']
                
                mmd_det_path = os.path.join(pdf_output_dir, pdf_filename.replace('.pdf', '_det.mmd'))
                mmd_path = os.path.join(pdf_output_dir, pdf_filename.replace('.pdf', '_det.mmd').replace('_det.mmd', '.mmd'))
                pdf_out_path = os.path.join(pdf_output_dir, pdf_filename.replace('.pdf', '_layouts.pdf'))
                
                contents_det = ''
                contents = ''
                draw_images = []
                jdx = 0
                
                # Process each image for this PDF
                for img in pdf_images:
                    output = outputs_list[image_idx]
                    content = output.outputs[0].text

                    if '<｜end▁of▁sentence｜>' in content:
                        content = content.replace('<｜end▁of▁sentence｜>', '')
                    else:
                        if SKIP_REPEAT:
                            image_idx += 1
                            continue

                    page_num = f'\n<--- Page Split --->'
                    contents_det += content + f'\n{page_num}\n'

                    image_draw = img.copy()
                    matches_ref, matches_images, mathes_other = re_match(content)
                    result_image = process_image_with_refs(image_draw, matches_ref, jdx, pdf_output_dir)
                    draw_images.append(result_image)

                    for idx, a_match_image in enumerate(matches_images):
                        content = content.replace(a_match_image, f'![](images/{jdx}_{idx}.jpg)\n')

                    for idx, a_match_other in enumerate(mathes_other):
                        content = content.replace(a_match_other, '').replace('\\coloneqq', ':=').replace('\\eqqcolon', '=:').replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')

                    contents += content + f'\n{page_num}\n'
                    jdx += 1
                    image_idx += 1
                
                # Write outputs for this PDF
                with open(mmd_det_path, 'w', encoding='utf-8') as afile:
                    afile.write(contents_det)
                with open(mmd_path, 'w', encoding='utf-8') as afile:
                    afile.write(contents)
                pil_to_pdf_img2pdf(draw_images, pdf_out_path)
                
                logger.info(f"OCR succeeded for {pdf_filename}")
                total_success += 1
                
            except Exception as e:
                logger.error(f"OCR failed for {pdf_filename}: {e}")
                total_failed += 1
                image_idx += len(pdf_info['images'])  # Skip these images in outputs_list
    
    return total_success, total_failed


print("Pre-allocation....")
# Pre-allocate KV cache with a dry run on dummy input
dummy_image = Image.new('RGB', (1024,1024), color='white')
dummy_input = process_single_image(dummy_image)
_ = llm.generate([dummy_input], sampling_params=sampling_params)
torch.cuda.synchronize()

# Lazy import
run_dpsk_ocr_pdf = None

ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, 'pdfs')
OCR_RESULTS_DIR = os.path.join(BASE_DIR, 'ocr_results')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

os.makedirs(OCR_RESULTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logger for OCR processor
logger = logging.getLogger("infra_ocr")
logger.setLevel(logging.INFO)
ocr_log_file = os.path.join(LOG_DIR, "ocr_processor.log")
fh = logging.FileHandler(ocr_log_file)
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(fh)

# Summary file for OCR results
SUMMARY_LOG = os.path.join(LOG_DIR, 'ocr_summary.jsonl')

SCRIPT_DIR = os.path.join(BASE_DIR, '..')
sys.path.insert(0, SCRIPT_DIR)

# Lazy import
run_dpsk_ocr_pdf = None


def run_ocr_on_pdf(pdf_path, output_dir):
    """Run OCR on a single PDF"""
    logger.info(f"Starting OCR for {pdf_path} -> {output_dir}")
    start_ts = datetime.utcnow().isoformat()

    try:
        process_batched_pdfs([(os.path.basename(pdf_path), pdf_path)], output_dir)
        end_ts = datetime.utcnow().isoformat()
        logger.info(f"OCR succeeded for {pdf_path} (output dir: {output_dir})")
        return True, "Success"
    except Exception as e:
        end_ts = datetime.utcnow().isoformat()
        logger.error(f"OCR failed for {pdf_path}: {e}")
        return False, str(e)


def main():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]

    print(f'Found {len(pdf_files)} PDFs to process')

    # Batch PDFs for better GPU utilization - limit to prevent OOM
    pdf_batch_size = 16  # Process 16 PDFs at a time (adjust based on average PDF size)
    max_images_per_batch = 2000  # Max images per LLM call (higher = better GPU util, but risk of OOM)
    print(f'Batch settings: {pdf_batch_size} PDFs per batch, max {max_images_per_batch} images per LLM call')
    total_failed = 0
    total_processed = 0

    with tqdm(total=len(pdf_files), desc="Processing OCR") as pbar:
        for i in range(0, len(pdf_files), pdf_batch_size):
            batch_files = pdf_files[i:i + pdf_batch_size]
            batch_data = [(f, os.path.join(PDF_DIR, f)) for f in batch_files]
            
            try:
                success_count, failed_count = process_batched_pdfs(batch_data, OCR_RESULTS_DIR, max_images_per_batch)
                total_processed += success_count
                total_failed += failed_count
                
                # Log per-batch results
                for pdf_file in batch_files:
                    paper_id = os.path.splitext(pdf_file)[0]
                    output_dir = os.path.join(OCR_RESULTS_DIR, paper_id)
                    log_path = os.path.join(LOG_DIR, f"{paper_id}.log")
                    
                    success = (pdf_file in [f for f, _ in batch_data[:success_count]])
                    
                    try:
                        with open(log_path, 'w') as f:
                            f.write(f"pdf: {os.path.join(PDF_DIR, pdf_file)}\n")
                            f.write(f"output_dir: {output_dir}\n")
                            f.write(f"success: {success}\n")
                            f.write(f"timestamp: {datetime.utcnow().isoformat()}\n\n")
                    except Exception as e:
                        logger.warning(f"Failed to write per-paper log for {paper_id}: {e}")

                    # Append summary record
                    record = {
                        'id': paper_id,
                        'pdf_path': os.path.join(PDF_DIR, pdf_file),
                        'output_dir': output_dir,
                        'success': success,
                        'log_path': log_path,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    try:
                        with open(SUMMARY_LOG, 'a') as sf:
                            sf.write(json.dumps(record) + "\n")
                    except Exception as e:
                        logger.warning(f"Failed to write summary for {paper_id}: {e}")
                        
            except Exception as e:
                logger.error(f"Batch processing failed for batch starting at {i}: {e}")
                total_failed += len(batch_files)
            
            pbar.update(len(batch_files))
            pbar.set_postfix({"processed": total_processed, "failed": total_failed})

    logger.info(f"OCR processing complete. total={len(pdf_files)}, processed={total_processed}, failed={total_failed}")

if __name__ == "__main__":
    main()