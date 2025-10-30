import os
import sys
import json
from pathlib import Path
from datasets import Dataset, Image

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

    # Collect all data
    all_paper_ids = []
    all_image_paths = []
    all_markdowns = []
    all_metadata = []

    for paper_dir in ocr_results_dir.iterdir():
        if paper_dir.is_dir():
            paper_id = paper_dir.name
            images_dir = paper_dir / "images"
            mmd_file = paper_dir / f"{paper_id}.mmd"
            if images_dir.exists() and mmd_file.exists():
                # Load markdown
                with open(mmd_file, 'r', encoding='utf-8') as f:
                    markdown = f.read()

                # Load metadata if available (several possible locations)
                metadata = {}
                # 1) paper_dir/<paper_id>.json
                candidate1 = paper_dir / f"{paper_id}.json"
                # 2) paper_dir/metadata.json
                candidate2 = paper_dir / "metadata.json"
                # 3) top-level metadata/<paper_id>.json
                candidate3 = base_dir / "metadata" / f"{paper_id}.json"

                for cand in (candidate1, candidate2, candidate3):
                    if cand.exists():
                        try:
                            with open(cand, 'r', encoding='utf-8') as mf:
                                metadata = json.load(mf)
                                print(f"Loaded metadata for {paper_id} from {cand}")
                                break
                        except Exception as me:
                            print(f"Failed to read metadata {cand} for {paper_id}: {me}")
                            # keep trying other candidates or fall back to empty dict

                # Load images
                image_paths = sorted(images_dir.glob("*.jpg"))
                if image_paths:
                    all_paper_ids.extend([paper_id] * len(image_paths))
                    all_image_paths.extend([str(p) for p in image_paths])
                    all_markdowns.extend([markdown] * len(image_paths))
                    all_metadata.extend([metadata] * len(image_paths))
                    print(f"Collected {len(image_paths)} images for {paper_id}")
                else:
                    print(f"No images for {paper_id}")
            else:
                print(f"Missing files for {paper_id}")

    if not all_image_paths:
        print("No data to upload")
        return

    # Create big dataset
    data = {
        "paper_id": all_paper_ids,
        "image": all_image_paths,  # Will be cast to Image
        "markdown": all_markdowns
    }

    # Include metadata column
    data["metadata"] = all_metadata

    dataset = Dataset.from_dict(data).cast_column("image", Image())

    # Push to Hub
    repo_id = "alphaXiv/alphaxiv-dataset"
    try:
        dataset.push_to_hub(repo_id, token=hf_token)
        print(f"Uploaded big dataset to {repo_id} with {len(all_image_paths)} images from {len(set(all_paper_ids))} papers")
    except Exception as e:
        print(f"Failed to upload dataset: {e}")

if __name__ == "__main__":
    main()
    if __name__ == "__main__":
        main()