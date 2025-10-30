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

from vllm import AsyncLLMEngine, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.model_executor.models.registry import ModelRegistry
import time
from deepseek_ocr import DeepseekOCRForCausalLM
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
from process.image_process import DeepseekOCRProcessor
from config import MODEL_PATH, INPUT_PATH, OUTPUT_PATH, PROMPT, CROP_MODE

ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

# Initialize VLLM engine once for better GPU utilization
engine = None
logits_processors = None
sampling_params = None

def initialize_vllm():
    global engine, logits_processors, sampling_params
    if engine is None:
        engine_args = AsyncEngineArgs(
            model=MODEL_PATH,
            hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
            block_size=256,
            max_model_len=8192,
            enforce_eager=False,
            trust_remote_code=True,  
            tensor_parallel_size=1,
            gpu_memory_utilization=0.75,
        )
        engine = AsyncLLMEngine.from_engine_args(engine_args)
        
        logits_processors = [NoRepeatNGramLogitsProcessor(ngram_size=30, window_size=90, whitelist_token_ids={128821, 128822})]
        
        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            logits_processors=logits_processors,
            skip_special_tokens=False,
        )
        logger.info("VLLM engine initialized")

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
    global run_dpsk_ocr_pdf
    if run_dpsk_ocr_pdf is None:
        import run_dpsk_ocr_pdf
    
    logger.info(f"Starting OCR for {pdf_path} -> {output_dir}")
    start_ts = datetime.utcnow().isoformat()

    try:
        run_dpsk_ocr_pdf.process_pdf_to_ocr(pdf_path, output_dir)
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
    initialize_vllm()  # Initialize VLLM once
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