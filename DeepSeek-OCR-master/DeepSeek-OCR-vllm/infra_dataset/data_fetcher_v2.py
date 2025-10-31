import requests
import json
import os
from tqdm import tqdm
import time
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
import fitz  # For PDF page count check

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

SESSION = requests.Session()

# Updated URLs for new API
ALL_PAPERS_URL = "https://api.alphaxiv.org/papers/v3/all"
METADATA_URL = "https://api.alphaxiv.org/papers/v3/{}"
PDF_URL = "https://fetcher.alphaxiv.org/v2/pdf/{}.pdf"

PAGE_SIZE = 100000  # Updated to match API limit
MAX_PAPERS = 100000  # Updated to 100000 as requested

def fetch_all_papers_page(skip, limit=100000):
    """Fetch universal IDs from the new API with pagination"""
    url = f"{ALL_PAPERS_URL}?skip={skip}&limit={limit}"

    headers = {
        'Accept': 'application/json',
        'User-Agent': 'DeepSeek-OCR-Dataset/1.0'
    }

    for attempt in range(2):  # Reduced from 3 to 2 attempts
        try:
            logger.info(f"Fetching all papers URL: {url}")
            response = SESSION.get(url, timeout=10, headers=headers)  # Reduced timeout from 15 to 10
            logger.info(f"All papers response status: {response.status_code}")
            if response.status_code == 200:
                data = None
                try:
                    data = response.json()
                except Exception as e:
                    logger.warning(f"Failed to parse JSON: {e}; text snippet: {response.text[:200]}")
                if data and 'universalIds' in data:
                    # Clean universal IDs by removing /metadata suffixes
                    cleaned_ids = []
                    for uid in data['universalIds']:
                        # Remove /metadata or /view suffixes if present
                        clean_id = uid.split('/')[0] if '/' in uid else uid
                        cleaned_ids.append(clean_id)
                    data['universalIds'] = cleaned_ids
                    return data
            else:
                logger.warning(f"Non-200 status: {response.status_code}; text: {response.text[:200]}")
        except Exception as e:
            logger.warning(f"All papers fetch attempt {attempt+1} failed: {e}")
        time.sleep(1)

    logger.error(f"Failed to fetch all papers page with skip={skip} after attempts")
    return None

def fetch_metadata(paper_id, retries=1):
    url = METADATA_URL.format(paper_id)
    for attempt in range(retries):
        try:
            response = SESSION.get(url, timeout=10)  # Reduced timeout from 15 to 10
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Metadata fetch {paper_id} attempt {attempt+1} failed: {e}")
            continue  # Removed sleep delay
    logger.error(f"Metadata fetch failed for {paper_id} after {retries} attempts")
    return None

def get_pdf_count():
    """Get the current number of PDF files in the pdfs directory"""
    if os.path.exists(PDF_DIR):
        return len([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])
    return 0

def download_pdf(paper_id, version, retries=1):
    # Try only v0 and v1 versions first (most common), then v2-v3 if needed
    version_priority = [0, 1, 2, 3]  # Reduced from 0-5 to 0-3, reordered for efficiency
    
    for v in version_priority:
        pdf_id = f"{paper_id}v{v}"
        pdf_path = os.path.join(PDF_DIR, f"{pdf_id}.pdf")
        if os.path.exists(pdf_path):
            logger.info(f"PDF already exists: {pdf_id}")
            return True, v, pdf_path

        url = PDF_URL.format(pdf_id)
        for attempt in range(retries):
            try:
                resp = SESSION.get(url, timeout=15, stream=True)  # Reduced timeout from 30 to 15
                if resp.status_code != 200:
                    logger.warning(f"PDF {pdf_id} attempt {attempt+1} returned status {resp.status_code}")
                    continue  # Removed sleep delay

                # stream to disk
                with open(pdf_path, 'wb') as f:
                    # Option 1: Stream in chunks (memory efficient for large files)
                    # for chunk in resp.iter_content(chunk_size=16384):
                    #     if chunk:
                    #         f.write(chunk)
                    #         total_bytes += len(chunk)

                    # Option 2: Write all at once (faster for smaller files)
                    content = resp.content
                    f.write(content)
                    total_bytes = len(content)

                if total_bytes < 1024:
                    logger.warning(f"PDF {pdf_id} too small ({total_bytes} bytes), removing")
                    try:
                        os.remove(pdf_path)
                    except Exception:
                        pass
                    continue  # Removed sleep delay

                logger.info(f"Downloaded {pdf_id} ({total_bytes} bytes)")
                return True, v, pdf_path
            except Exception as e:
                logger.warning(f"Download {pdf_id} attempt {attempt+1} failed: {e}")
                continue  # Removed sleep delay

        logger.info(f"No valid response for {pdf_id} after {retries} attempts, trying next version")

    logger.error(f"No version found for {paper_id}")
    return False, None, None

def process_paper(universal_id):
    """Process a single paper by its universal ID"""
    if not universal_id:
        print(f"Skipping empty universal id")
        return False

    # sanitize universal_id for filenames
    safe_key = str(universal_id).replace('/', '_')

    # Attempt to download using universal id only (v0..v5)
    success, actual_version, pdf_path = download_pdf(universal_id, 1)

    if not success:
        logger.info(f"Download failed for {universal_id}")
        record = {
            'id': universal_id,
            'status': 'download_failed',
            'reason': 'no_valid_pdf_version',
            'meta_path': None,
            'pdf_path': None,
            'pdf_version': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        with open(SUMMARY_LOG, 'a') as sf:
            sf.write(json.dumps(record) + "\n")
        return False

    # Check PDF page count
    try:
        doc = fitz.open(pdf_path)
        page_count = doc.page_count
        doc.close()
        if page_count > 50:
            logger.info(f"Skipping {universal_id}: PDF has {page_count} pages (>50)")
            if pdf_path:
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass
            record = {
                'id': universal_id,
                'status': 'skipped_page_count',
                'reason': f'page_count_{page_count}',
                'meta_path': None,
                'pdf_path': None,
                'pdf_version': None,
                'timestamp': datetime.utcnow().isoformat()
            }
            with open(SUMMARY_LOG, 'a') as sf:
                sf.write(json.dumps(record) + "\n")
            return False
    except Exception as e:
        logger.warning(f"Failed to check page count for {universal_id}: {e}")
        # If can't check, assume ok or skip? To be safe, skip
        if pdf_path:
            try:
                os.remove(pdf_path)
            except Exception:
                pass
        record = {
            'id': universal_id,
            'status': 'skipped_page_check_failed',
            'reason': str(e),
            'meta_path': None,
            'pdf_path': None,
            'pdf_version': None,
            'timestamp': datetime.utcnow().isoformat()
        }
        with open(SUMMARY_LOG, 'a') as sf:
            sf.write(json.dumps(record) + "\n")
        return False

    # Now fetch metadata
    metadata = fetch_metadata(universal_id)
    if not metadata:
        logger.info(f"Skipping {universal_id}: metadata fetch failed")
        # Remove PDF since we won't process it
        if pdf_path:
            try:
                os.remove(pdf_path)
            except Exception:
                pass
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

    # Only process if license contains Creative Commons
    license_url = metadata.get('license')
    if not license_url or 'creativecommons' not in license_url.lower():
        logger.info(f"Skipping {universal_id} due to license '{license_url}'")
        # Remove PDF
        if pdf_path:
            try:
                os.remove(pdf_path)
            except Exception:
                pass
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
    """Main function to fetch and process papers using the new all papers API"""
    unique_papers = set()
    total_pbar = tqdm(desc="PDFs downloaded", unit="pdf")

    skip = PAGE_SIZE  # Start from skip=10000
    batch_size = PAGE_SIZE  # 100000 IDs per batch

    while get_pdf_count() < MAX_PAPERS:
        logger.info(f"Fetching papers with skip={skip}, limit={batch_size}")

        # Fetch batch of universal IDs
        batch_data = fetch_all_papers_page(skip, batch_size)

        if not batch_data or 'universalIds' not in batch_data:
            logger.info(f"No more data available at skip={skip}")
            break

        universal_ids = batch_data['universalIds']
        if not universal_ids:
            logger.info(f"Empty universal IDs list at skip={skip}")
            break

        logger.info(f"Processing {len(universal_ids)} papers from skip={skip}")

        # Filter for new papers we haven't seen before
        new_ids = []
        for uid in universal_ids:
            uid_safe = str(uid).replace('/', '_')
            if uid_safe not in unique_papers:
                unique_papers.add(uid_safe)
                new_ids.append(uid)

        if not new_ids:
            logger.info(f"No new papers in this batch (skip={skip})")
            skip += 10000  # Increment skip by 10000
            continue

        logger.info(f"Processing {len(new_ids)} new papers from batch")

        # Process new papers in parallel
        cpu_count = os.cpu_count()
        with ThreadPoolExecutor(max_workers=cpu_count) as executor:
            futures = [executor.submit(process_paper, uid) for uid in new_ids]
            for future in as_completed(futures):
                future.result()

        # Update progress bar after processing this batch
        current_count = get_pdf_count()
        total_pbar.n = current_count
        total_pbar.refresh()

        # Add delay after every 1000 PDFs downloaded
        # if current_count > 0 and current_count % 1000 == 0:
        logger.info(f"Downloaded {current_count} PDFs, taking a 5-second break...")
        # time.sleep(5)

        # Check if we've reached the PDF limit
        if get_pdf_count() >= MAX_PAPERS:
            logger.info(f"Reached target PDF count ({get_pdf_count()}/{MAX_PAPERS}), stopping")
            break

        # Move to next batch - increment skip by 10000
        skip += PAGE_SIZE

        # Rate limiting between batches
        time.sleep(20)

    total_pbar.close()
    final_pdf_count = get_pdf_count()
    print(f"Collected {len(unique_papers)} unique papers, downloaded {final_pdf_count} PDFs")

if __name__ == "__main__":
    main()