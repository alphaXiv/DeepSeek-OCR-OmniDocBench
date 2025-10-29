# DeepSeek OCR Dataset Infrastructure

This folder contains the infrastructure for building a large-scale OCR dataset using DeepSeek OCR model.

## Folder Structure

- `pdfs/`: Downloaded PDF files
- `metadata/`: JSON metadata for each paper
- `ocr_results/`: OCR output markdown files
- `images/`: Extracted images from PDFs (if any)
- `logs/`: Processing logs

## Scripts

- `data_fetcher.py`: Fetches paper metadata and downloads PDFs from alphaXiv API
- `ocr_processor.py`: Runs DeepSeek OCR on downloaded PDFs
- `run_infra.sh`: Bash script to run the entire pipeline

## Usage

1. Make sure you have the required dependencies installed
2. Run `./run_infra.sh` to execute the full pipeline
3. Or run individual scripts as needed

## Configuration

- Adjust `MAX_PAPERS` in `data_fetcher.py` for the number of papers to fetch
- Modify concurrency in scripts based on your system resources
- Ensure GPU memory is sufficient for OCR processing