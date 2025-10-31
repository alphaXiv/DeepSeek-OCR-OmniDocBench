#!/bin/bash

# Exit on any error
set -e

# Trap to handle errors
trap 'echo "Error occurred at line $LINENO. Exiting..." >&2; exit 1' ERR

# Robust Infra Runner Script

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "Starting DeepSeek OCR Dataset Infrastructure"

# Install dependencies
echo "Installing dependencies..."
pip install huggingface_hub datasets

# Step 2: Fetch data
echo "Fetching papers and downloading PDFs..."
python data_fetcher.py

# Step 3: Upload PDFs to Hugging Face
echo "Uploading PDF dataset to Hugging Face Hub..."
./upload_pdfs.sh

# Step 4: Run OCR processing
echo "Running OCR on downloaded PDFs..."
python ocr_processor.py

# Step 5: Upload to Hugging Face
echo "Uploading OCR images to Hugging Face Hub..."
python upload_all_to_hf.py

echo "Infrastructure run complete!"