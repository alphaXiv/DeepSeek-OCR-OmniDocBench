import requests
import json
import os
from tqdm import tqdm
import time
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, 'pdfs')
METADATA_DIR = os.path.join(BASE_DIR, 'metadata')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logger
logger = logging.getLogger("infra_dataset")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(os.path.join(LOG_DIR, "fetcher.log"))
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(fh)

# Summary JSONL for consolidated per-paper records
SUMMARY_LOG = os.path.join(LOG_DIR, 'summary.jsonl')

# Shared requests session
SESSION = requests.Session()

FEED_URL = "https://api.alphaxiv.org/papers/v2/feed"
METADATA_URL = "https://api.alphaxiv.org/papers/v3/{}"
PDF_URL = "https://fetcher.alphaxiv.org/v2/pdf/{}{}.pdf"

PAGE_SIZE = 100
MAX_PAPERS = 100  # Start with 100 for testing

def fetch_feed_page(page_num):
    # Build query string for params, but include topics as a pre-encoded literal to avoid
    # requests double-encoding '%5B%5D' into '%255B%255D'.
    params = {
        'pageNum': page_num,
        'sortBy': 'Hot',
        'pageSize': PAGE_SIZE,
    }

    # Encode params except topics
    qs = urlencode(params)
    # Append topics as already-encoded '%5B%5D' to avoid double-encoding
    url = f"{FEED_URL}?{qs}&topics=%5B%5D"

    # simple retries for feed pages
    for attempt in range(3):
        try:
            response = SESSION.get(url, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Feed page {page_num} attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    logger.error(f"Failed to fetch feed page {page_num} after 3 attempts")
    return None

def fetch_metadata(paper_id, retries=3):
    url = METADATA_URL.format(paper_id)
    for attempt in range(retries):
        try:
            response = SESSION.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Metadata fetch {paper_id} attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    logger.error(f"Metadata fetch failed for {paper_id} after {retries} attempts")
    return None

def download_pdf(paper_id, version, retries=3):
    # Try versions from v0 to v5, use the first one that works
    for v in range(6):  # 0 to 5
        pdf_id = f"{paper_id}v{v}"
        pdf_path = os.path.join(PDF_DIR, f"{pdf_id}.pdf")
        if os.path.exists(pdf_path):
            logger.info(f"PDF already exists: {pdf_id}")
            return True, v, pdf_path

        url = PDF_URL.format(pdf_id, version)
        for attempt in range(retries):
            try:
                resp = SESSION.get(url, timeout=60, stream=True)
                if resp.status_code != 200:
                    logger.warning(f"PDF {pdf_id} attempt {attempt+1} returned status {resp.status_code}")
                    time.sleep(2 ** attempt)
                    continue

                # stream to disk
                total_bytes = 0
                with open(pdf_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_bytes += len(chunk)

                if total_bytes < 1024:
                    logger.warning(f"PDF {pdf_id} too small ({total_bytes} bytes), removing")
                    try:
                        os.remove(pdf_path)
                    except Exception:
                        pass
                    time.sleep(2 ** attempt)
                    continue

                logger.info(f"Downloaded {pdf_id} ({total_bytes} bytes)")
                return True, v, pdf_path
            except Exception as e:
                logger.warning(f"Download {pdf_id} attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)
                continue

        logger.info(f"No valid response for {pdf_id} after {retries} attempts, trying next version")

    logger.error(f"No version found for {paper_id}")
    return False, None, None

def process_paper(paper):
    # Use universal id only (required): support both field names
    universal_id = paper.get('universal_paper_id') or paper.get('universalId')
    if not universal_id:
        print(f"Skipping paper without universal id: {paper.get('id')}")
        return False

    # sanitize universal_id for filenames
    safe_key = str(universal_id).replace('/', '_')
    # Fetch metadata using universal id only (with retries)
    metadata = fetch_metadata(universal_id)
    if not metadata:
        logger.info(f"Skipping {universal_id}: metadata fetch failed")
        # write summary
        record = {
            'id': universal_id,
            'status': 'metadata_fetch_failed',
            'reason': 'metadata_fetch_failed',
            'meta_path': None,
            'pdf_path': None,
            'pdf_version': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        with open(SUMMARY_LOG, 'a') as sf:
            sf.write(json.dumps(record) + "\n")
        return False

    # Save metadata using the safe universal id (always save for record)
    meta_path = os.path.join(METADATA_DIR, f"{safe_key}.json")
    try:
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.warning(f"Error saving metadata for {safe_key}: {e}")

    # Only process (download PDFs) if license is CC-BY-4.0
    license_url = metadata.get('license')
    allowed_license = "http://creativecommons.org/licenses/by/4.0/"
    if not license_url or license_url.strip() != allowed_license:
        logger.info(f"Skipping {universal_id} due to license '{license_url}'")
        record = {
            'id': universal_id,
            'status': 'skipped_license',
            'reason': license_url,
            'meta_path': meta_path,
            'pdf_path': None,
            'pdf_version': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        with open(SUMMARY_LOG, 'a') as sf:
            sf.write(json.dumps(record) + "\n")
        return False

    # Determine a suggested starting version if available (e.g., 'v1')
    suggested_version = None
    if isinstance(paper.get('versionLabel'), str):
        try:
            suggested_version = int(paper.get('versionLabel').lstrip('vV'))
        except Exception:
            suggested_version = None
    elif 'version' in paper:
        try:
            suggested_version = int(paper.get('version'))
        except Exception:
            suggested_version = None

    # Attempt to download using universal id only (v0..v5)
    success, actual_version, pdf_path = download_pdf(universal_id, suggested_version or 1)

    if not success:
        logger.info(f"Download failed for {universal_id}")
        record = {
            'id': universal_id,
            'status': 'download_failed',
            'reason': 'no_valid_pdf_version',
            'meta_path': meta_path,
            'pdf_path': None,
            'pdf_version': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        with open(SUMMARY_LOG, 'a') as sf:
            sf.write(json.dumps(record) + "\n")
        return False

    # Ensure metadata exists for this pdf (it does because we fetched earlier). Attach version and save
    try:
        metadata['pdf_version'] = actual_version
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception:
        pass

    record = {
        'id': universal_id,
        'status': 'downloaded',
        'reason': None,
        'meta_path': meta_path,
        'pdf_path': pdf_path,
        'pdf_version': actual_version,
        'timestamp': datetime.utcnow().isoformat()
    }
    with open(SUMMARY_LOG, 'a') as sf:
        sf.write(json.dumps(record) + "\n")

    return True

def main():
    unique_papers = set()
    page_num = 0
    
    with tqdm(total=MAX_PAPERS, desc="Fetching papers") as pbar:
        while len(unique_papers) < MAX_PAPERS:
            feed_data = fetch_feed_page(page_num)
            if not feed_data or 'data' not in feed_data:
                print(f"No more data at page {page_num}")
                break
            
            papers = feed_data['data']
            if not papers:
                break
            
            new_papers = []
            for paper in papers:
                pid = paper.get('universal_paper_id') or paper.get('universalId')
                if not pid:
                    # skip papers without universal id
                    continue
                # sanitize
                pid_safe = str(pid).replace('/', '_')
                if pid_safe not in unique_papers:
                    unique_papers.add(pid_safe)
                    new_papers.append(paper)
                    pbar.update(1)
                    if len(unique_papers) >= MAX_PAPERS:
                        break
            
            # Process in parallel (limit workers based on CPU count)
            cpu_count = os.cpu_count() or 1
            max_workers = max(1, cpu_count // 2)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_paper, paper) for paper in new_papers]
                for future in as_completed(futures):
                    future.result()
            
            page_num += 1
            time.sleep(1)  # Rate limiting
    
    print(f"Collected {len(unique_papers)} unique papers")

if __name__ == "__main__":
    main()