import os
import json
import sys
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime

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
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]

    logger.info(f"Found {len(pdf_files)} PDFs to process")
    print(f"Found {len(pdf_files)} PDFs to process")

    max_workers = 1  # Keep sequential for GPU
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_pdf, pdf) for pdf in pdf_files]

        with tqdm(total=len(pdf_files), desc="Processing OCR") as pbar:
            failed = 0
            for future in as_completed(futures):
                success = future.result()
                pbar.update(1)
                if not success:
                    failed += 1
                    pbar.set_postfix({"failed": failed})
    logger.info(f"OCR processing complete. total={len(pdf_files)}, failed={failed}")

if __name__ == "__main__":
    main()