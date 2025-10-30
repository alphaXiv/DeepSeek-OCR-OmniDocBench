#!/bin/bash

# PDF Upload Script for HuggingFace
# This script installs dependencies and uploads PDFs to HF dataset

set -e

echo "🚀 PDF Upload to HuggingFace Dataset"
echo "===================================="

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ]; then
    echo "❌ Error: HF_TOKEN environment variable not set"
    echo "Please set it with: export HF_TOKEN=your_token_here"
    exit 1
fi

# Install requirements if needed
if ! python -c "import datasets, huggingface_hub, tqdm" 2>/dev/null; then
    echo "📦 Installing required packages..."
    pip install -r requirements-pdf-upload.txt
fi

# Run the upload script
echo "⬆️ Starting upload..."
python upload_pdfs_to_hf.py "$@"

echo "✅ Upload completed!"