import os
import sys
from huggingface_hub import HfApi, create_repo
from pathlib import Path
import argparse

def upload_paper_images_to_hf(paper_id, hf_token, org_name="alphaXiv"):
    """
    Upload OCR images for a paper to Hugging Face Hub as a dataset.
    """
    base_dir = Path(__file__).parent
    images_dir = base_dir / "ocr_results" / paper_id / "images"

    if not images_dir.exists():
        print(f"No images directory found for {paper_id}")
        return False

    # Create repo name
    repo_name = f"{paper_id}-ocr-images"
    repo_id = f"{org_name}/{repo_name}"

    # Create repo
    try:
        create_repo(repo_id, token=hf_token, repo_type="dataset", private=False)
        print(f"Created repo: {repo_id}")
    except Exception as e:
        print(f"Repo might already exist or error: {e}")

    # Upload images
    api = HfApi(token=hf_token)
    try:
        api.upload_folder(
            folder_path=str(images_dir),
            repo_id=repo_id,
            repo_type="dataset",
            path_in_repo="images"
        )
        print(f"Uploaded images for {paper_id} to {repo_id}")
    except Exception as e:
        print(f"Failed to upload images for {paper_id}: {e}")
        return False

    # Create a simple dataset card
    readme_content = f"""---
dataset_info:
  features:
  - name: image
    dtype: image
  splits:
  - name: train
    num_bytes: 0
    num_examples: {len(list(images_dir.glob('*.jpg')))}
  download_size: 0
  dataset_size: 0
---

# {paper_id} OCR Images

This dataset contains OCR-extracted images from the paper {paper_id}.

Images are extracted during the OCR process using DeepSeek-OCR.
"""

    readme_path = base_dir / "temp_readme.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    try:
        api.upload_file(
            path_or_fileobj=str(readme_path),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset"
        )
        print(f"Uploaded README for {paper_id}")
    except Exception as e:
        print(f"Failed to upload README for {paper_id}: {e}")
    finally:
        if readme_path.exists():
            readme_path.unlink()

    return True

def main():
    parser = argparse.ArgumentParser(description="Upload OCR images to Hugging Face Hub")
    parser.add_argument("paper_id", help="Paper ID to upload")
    parser.add_argument("--token", help="Hugging Face token", default=os.environ.get("HF_TOKEN"))
    parser.add_argument("--org", help="Organization name", default="alphaXiv")

    args = parser.parse_args()

    if not args.token:
        print("HF_TOKEN not provided. Set HF_TOKEN environment variable or use --token")
        sys.exit(1)

    success = upload_paper_images_to_hf(args.paper_id, args.token, args.org)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()