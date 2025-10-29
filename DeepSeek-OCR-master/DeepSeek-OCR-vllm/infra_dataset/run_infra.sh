#!/bin/bash

# Robust Infra Runner Script

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "Starting DeepSeek OCR Dataset Infrastructure"


# Step 2: Fetch data
echo "Fetching papers and downloading PDFs..."
python data_fetcher.py

# Step 3: Run OCR processing
echo "Running OCR on downloaded PDFs..."
python ocr_processor.py

echo "Infrastructure run complete!"