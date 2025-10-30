import os
import sys
from pathlib import Path
import subprocess

def main():
    base_dir = Path(__file__).parent
    ocr_results_dir = base_dir / "ocr_results"

    if not ocr_results_dir.exists():
        print("No ocr_results directory found")
        return

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("HF_TOKEN not set")
        return

    for paper_dir in ocr_results_dir.iterdir():
        if paper_dir.is_dir():
            paper_id = paper_dir.name
            images_dir = paper_dir / "images"
            mmd_file = paper_dir / f"{paper_id}.mmd"
            if images_dir.exists() and mmd_file.exists() and any(images_dir.glob("*.jpg")):
                print(f"Uploading dataset for {paper_id}")
                result = subprocess.run([
                    sys.executable, "upload_to_hf.py", paper_id, "--token", hf_token
                ], cwd=base_dir)
                if result.returncode != 0:
                    print(f"Failed to upload {paper_id}")
            else:
                print(f"No images or markdown for {paper_id}")

if __name__ == "__main__":
    main()