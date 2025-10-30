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


def process_pdf_to_ocr(input_path, output_path):
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(f'{output_path}/images', exist_ok=True)
    
    print('PDF loading .....')

    images = pdf_to_images_high_quality(input_path)

    prompt = PROMPT

    # batch_inputs = []
    NUM_WORKERS = os.cpu_count()
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:  
        batch_inputs = list(tqdm(
            executor.map(process_single_image, images),
            total=len(images),
            desc="Pre-processed images"
        ))

    outputs_list = llm.generate(
        batch_inputs,
        sampling_params=sampling_params
    )

    mmd_det_path = output_path + '/' + input_path.split('/')[-1].replace('.pdf', '_det.mmd')
    mmd_path = output_path + '/' + input_path.split('/')[-1].replace('pdf', 'mmd')
    pdf_out_path = output_path + '/' + input_path.split('/')[-1].replace('.pdf', '_layouts.pdf')
    contents_det = ''
    contents = ''
    draw_images = []
    jdx = 0
    for output, img in zip(outputs_list, images):
        content = output.outputs[0].text

        if '<｜end▁of▁sentence｜>' in content: # repeat no eos
            content = content.replace('<｜end▁of▁sentence｜>', '')
        else:
            if SKIP_REPEAT:
                continue

        
        page_num = f'\n<--- Page Split --->'

        contents_det += content + f'\n{page_num}\n'

        image_draw = img.copy()

        matches_ref, matches_images, mathes_other = re_match(content)
        # print(matches_ref)
        result_image = process_image_with_refs(image_draw, matches_ref, jdx, output_path)


        draw_images.append(result_image)


        for idx, a_match_image in enumerate(matches_images):
            content = content.replace(a_match_image, f'![](images/' + str(jdx) + '_' + str(idx) + '.jpg)\n')

        for idx, a_match_other in enumerate(mathes_other):
            content = content.replace(a_match_other, '').replace('\\coloneqq', ':=').replace('\\eqqcolon', '=:').replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')


        contents += content + f'\n{page_num}\n'


        jdx += 1

    with open(mmd_det_path, 'w', encoding='utf-8') as afile:
        afile.write(contents_det)

    with open(mmd_path, 'w', encoding='utf-8') as afile:
        afile.write(contents)


    pil_to_pdf_img2pdf(draw_images, pdf_out_path)


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
        process_pdf_to_ocr(pdf_path, output_dir)
        end_ts = datetime.utcnow().isoformat()
        logger.info(f"OCR succeeded for {pdf_path} (output dir: {output_dir})")
        return True, "Success"
    except Exception as e:
        end_ts = datetime.utcnow().isoformat()
        logger.error(f"OCR failed for {pdf_path}: {e}")
        return False, str(e)

def process_pdf(pdf_file):
    pdf_path = os.path.join(PDF_DIR, pdf_file)
    paper_id = os.path.splitext(pdf_file)[0]
    
    # Create output dir for this paper
    output_dir = os.path.join(OCR_RESULTS_DIR, paper_id)
    os.makedirs(output_dir, exist_ok=True)
    
    success, output = run_ocr_on_pdf(pdf_path, output_dir)

    log_path = os.path.join(LOG_DIR, f"{paper_id}.log")
    try:
        with open(log_path, 'w') as f:
            f.write(f"pdf: {pdf_path}\n")
            f.write(f"output_dir: {output_dir}\n")
            f.write(f"success: {success}\n")
            f.write(f"timestamp: {datetime.utcnow().isoformat()}\n\n")
            f.write(output or '')
    except Exception as e:
        logger.warning(f"Failed to write per-paper log for {paper_id}: {e}")

    # Append summary record
    record = {
        'id': paper_id,
        'pdf_path': pdf_path,
        'output_dir': output_dir,
        'success': bool(success),
        'log_path': log_path,
        'timestamp': datetime.utcnow().isoformat()
    }
    try:
        with open(SUMMARY_LOG, 'a') as sf:
            sf.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write summary for {paper_id}: {e}")

    return success

def main():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]

    logger.info(f"Found {len(pdf_files)} PDFs to process")
    print(f"Found {len(pdf_files)} PDFs to process")

    batch_size = 4  # Process PDFs in batches for better GPU utilization
    total_failed = 0

    with tqdm(total=len(pdf_files), desc="Processing OCR") as pbar:
        for i in range(0, len(pdf_files), batch_size):
            batch = pdf_files[i:i + batch_size]
            for pdf in batch:
                success = process_pdf(pdf)
                pbar.update(1)
                if not success:
                    total_failed += 1
                    pbar.set_postfix({"failed": total_failed})

    logger.info(f"OCR processing complete. total={len(pdf_files)}, failed={total_failed}")

if __name__ == "__main__":
    main()