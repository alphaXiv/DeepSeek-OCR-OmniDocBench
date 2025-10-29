import os
import json
import subprocess
import sys
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, 'pdfs')
OCR_RESULTS_DIR = os.path.join(BASE_DIR, 'ocr_results')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

os.makedirs(OCR_RESULTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Path to the run_dpsk_ocr_pdf.py script
SCRIPT_DIR = os.path.join(BASE_DIR, '..')
OCR_SCRIPT = os.path.join(SCRIPT_DIR, 'run_dpsk_ocr_pdf.py')

def run_ocr_on_pdf(pdf_path, output_dir):
    """Run OCR on a single PDF"""
    try:
        # Modify config for this PDF
        config_path = os.path.join(SCRIPT_DIR, 'config.py')
        
        # Read current config
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Backup original
        backup = config_content
        
        # Modify INPUT_PATH and OUTPUT_PATH
        modified_config = config_content.replace(
            "INPUT_PATH = ''", 
            f"INPUT_PATH = '{pdf_path}'"
        ).replace(
            "OUTPUT_PATH = ''", 
            f"OUTPUT_PATH = '{output_dir}'"
        )
        
        # Write modified config
        with open(config_path, 'w') as f:
            f.write(modified_config)
        
        # Run the OCR script
        result = subprocess.run([
            sys.executable, OCR_SCRIPT
        ], cwd=SCRIPT_DIR, capture_output=True, text=True, timeout=7200)
        
        # Restore config
        with open(config_path, 'w') as f:
            f.write(backup)
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    
    except Exception as e:
        return False, str(e)

def process_pdf(pdf_file):
    pdf_path = os.path.join(PDF_DIR, pdf_file)
    paper_id = os.path.splitext(pdf_file)[0]
    
    # Create output dir for this paper
    output_dir = os.path.join(OCR_RESULTS_DIR, paper_id)
    os.makedirs(output_dir, exist_ok=True)
    
    success, output = run_ocr_on_pdf(pdf_path, output_dir)
    
    log_path = os.path.join(LOG_DIR, f"{paper_id}.log")
    with open(log_path, 'w') as f:
        f.write(f"Success: {success}\n")
        f.write(output)
    
    return success

def main():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    
    print(f"Found {len(pdf_files)} PDFs to process")
    
    with ThreadPoolExecutor(max_workers=4) as executor:  # Limit concurrency for GPU
        futures = [executor.submit(process_pdf, pdf) for pdf in pdf_files]
        
        with tqdm(total=len(pdf_files), desc="Processing OCR") as pbar:
            for future in as_completed(futures):
                success = future.result()
                pbar.update(1)
                if not success:
                    pbar.set_postfix({"failed": pbar.postfix.get("failed", 0) + 1})

if __name__ == "__main__":
    main()