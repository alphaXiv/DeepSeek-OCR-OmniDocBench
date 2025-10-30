import os
import sys
from pathlib import Path
from huggingface_hub import HfApi, create_repo
from datasets import Dataset, Image
import argparse

def upload_paper_to_hf_dataset(paper_id, hf_token, org_name="alphaXiv"):
    """
    Upload OCR images and markdown as a Hugging Face dataset with columns: paper_id, images, markdown.
    """
    base_dir = Path(__file__).parent
    ocr_dir = base_dir / "ocr_results" / paper_id
    images_dir = ocr_dir / "images"
    mmd_file = ocr_dir / f"{paper_id}.mmd"

    if not images_dir.exists() or not mmd_file.exists():
        print(f"Missing images or markdown for {paper_id}")
        return False

    # Load markdown
    with open(mmd_file, 'r', encoding='utf-8') as f:
        markdown = f.read()

    # Load images
    image_paths = sorted(images_dir.glob("*.jpg"))
    if not image_paths:
        print(f"No images for {paper_id}")
        return False

    # Create dataset row
    data = {
        "paper_id": [paper_id] * len(image_paths),
        "image": [str(p) for p in image_paths],  # Will be loaded as Image feature
        "markdown": [markdown] * len(image_paths)  # Same markdown for all images
    }

    # Create Dataset
    dataset = Dataset.from_dict(data).cast_column("image", Image())

    # Push to Hub
    repo_id = f"{org_name}/{paper_id}-ocr-dataset"
    try:
        dataset.push_to_hub(repo_id, token=hf_token)
        print(f"Uploaded dataset for {paper_id} to {repo_id}")
    except Exception as e:
        print(f"Failed to upload dataset for {paper_id}: {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(description="Upload OCR dataset to Hugging Face Hub")
    parser.add_argument("paper_id", help="Paper ID to upload")
    parser.add_argument("--token", help="Hugging Face token", default=os.environ.get("HF_TOKEN"))
    parser.add_argument("--org", help="Organization name", default="alphaXiv")

    args = parser.parse_args()

    if not args.token:
        print("HF_TOKEN not provided. Set HF_TOKEN environment variable or use --token")
        sys.exit(1)

    success = upload_paper_to_hf_dataset(args.paper_id, args.token, args.org)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
