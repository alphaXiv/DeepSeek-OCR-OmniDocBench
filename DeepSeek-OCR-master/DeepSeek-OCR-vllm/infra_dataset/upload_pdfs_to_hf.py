#!/usr/bin/env python3
"""
Script to upload downloaded PDFs to HuggingFace dataset.
Creates a dataset containing the original PDF files for archival and sharing.
"""

import os
import sys
from pathlib import Path
from datasets import Dataset
import argparse
from huggingface_hub import HfApi, create_repo
from tqdm import tqdm

def create_pdf_dataset(pdf_dir: Path, dataset_name: str = "alphaxiv-pdfs", org_name: str = "alphaXiv"):
    """
    Create and upload a HuggingFace dataset containing PDF files.

    Args:
        pdf_dir: Directory containing PDF files
        dataset_name: Name for the dataset on HuggingFace
        org_name: HuggingFace organization/user name
    """

    # Get HF token
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("❌ Error: HF_TOKEN environment variable not set")
        print("Please set it with: export HF_TOKEN=your_token_here")
        return False

    # Find all PDF files
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_dir}")
        return False

    print(f"📁 Found {len(pdf_files)} PDF files")

    # Prepare dataset data
    paper_ids = []
    pdf_paths = []
    file_sizes = []

    for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
        paper_id = pdf_path.stem  # filename without extension
        file_size = pdf_path.stat().st_size

        paper_ids.append(paper_id)
        pdf_paths.append(str(pdf_path))
        file_sizes.append(file_size)

    # Create dataset
    data = {
        "paper_id": paper_ids,
        "pdf": pdf_paths,  # Will be loaded as binary files
        "file_size": file_sizes
    }

    print("📦 Creating dataset...")
    dataset = Dataset.from_dict(data)

    # Create repo if it doesn't exist
    repo_id = f"{org_name}/{dataset_name}"
    api = HfApi()

    try:
        # Check if repo exists
        api.repo_info(repo_id, token=hf_token)
        print(f"📋 Repository {repo_id} exists")
    except Exception:
        # Create repo
        print(f"🆕 Creating repository {repo_id}...")
        create_repo(
            repo_id=repo_id,
            token=hf_token,
            repo_type="dataset",
            private=False
        )

    # Upload dataset
    print(f"⬆️ Uploading dataset to {repo_id}...")
    try:
        dataset.push_to_hub(
            repo_id=repo_id,
            token=hf_token,
            commit_message=f"Upload {len(pdf_files)} PDF files",
            private=False
        )
        print(f"✅ Successfully uploaded dataset to https://huggingface.co/datasets/{repo_id}")
        print(f"📊 Dataset contains {len(pdf_files)} PDFs")
        print(f"📏 Total size: {sum(file_sizes) / (1024**3):.2f} GB")
        return True

    except Exception as e:
        print(f"❌ Failed to upload dataset: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Upload PDFs to HuggingFace dataset")
    parser.add_argument(
        "--pdf-dir",
        type=str,
        default="./pdfs",
        help="Directory containing PDF files (default: ./pdfs)"
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="alphaxiv-pdfs",
        help="Name for the dataset on HuggingFace (default: alphaxiv-pdfs)"
    )
    parser.add_argument(
        "--org-name",
        type=str,
        default="alphaXiv",
        help="HuggingFace organization/user name (default: alphaXiv)"
    )

    args = parser.parse_args()

    # Convert to absolute path
    pdf_dir = Path(args.pdf_dir).resolve()

    if not pdf_dir.exists():
        print(f"❌ PDF directory {pdf_dir} does not exist")
        return 1

    print("🚀 Starting PDF upload to HuggingFace dataset")
    print(f"📁 PDF directory: {pdf_dir}")
    print(f"📦 Dataset name: {args.dataset_name}")
    print(f"🏢 Organization: {args.org_name}")
    print()

    success = create_pdf_dataset(pdf_dir, args.dataset_name, args.org_name)

    if success:
        print("\n🎉 Upload completed successfully!")
        return 0
    else:
        print("\n💥 Upload failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())