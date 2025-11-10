import requests
import time
import json
import os
from tqdm import tqdm 

pdf_dir = os.listdir('images_to_pdf')
                     
url = "https://www.datalab.to/api/v1/ocr"
headers = {"X-Api-Key" :  "..."}
max_polls = 300
max_retries = 3


def get_data(pdf_path):
    form_data = {
        'file': ('document.pdf', open(pdf_path, 'rb'), 'application/pdf'),
        'mode': (None, 'balanced'), # or 'accurate' for Chandra
        'output_format': (None, 'markdown') 
    }
    
    # Submit request
    response = requests.post(url, files=form_data, headers=headers)
    data = response.json()

    print(data)
    # Poll for completion
    check_url = data["request_check_url"]

    return check_url

# Create output directory if it doesn't exist
os.makedirs('output_results', exist_ok=True)

# Get list of already processed files
processed_files = set(os.listdir('output_results'))
processed_pdfs = set(os.path.splitext(f)[0] + '.pdf' for f in processed_files if f.endswith('.md'))

for i in tqdm(range(len(pdf_dir))):
    pdf_filename = pdf_dir[i]
    
    # Skip if already processed
    if pdf_filename in processed_pdfs:
        print(f"\nSkipping (already processed): {pdf_filename}")
        continue
    
    # Skip non-PDF files
    if not pdf_filename.lower().endswith('.pdf'):
        continue
    
    pdf_path = f'images_to_pdf/{pdf_filename}'
    
    # Retry logic
    for retry in range(max_retries):
        try:
            check_url = get_data(pdf_path)
            
            for j in range(max_polls):
                time.sleep(2)
                response = requests.get(check_url, headers=headers)
                data = response.json()
                
                if data["status"] == "complete":
                    full_text = ''
                    for page in data['pages']:
                        for lines in page['text_lines']:  
                            full_text += lines['text']
                    
                    # Save the result as .md file
                    output_filename = os.path.splitext(pdf_filename)[0] + '.md'
                    output_path = f'output_results/{output_filename}'
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(full_text)
                    
                    print(f"\nCompleted: {pdf_filename} -> {output_filename}")
                    break
                elif data["status"] == "failed":
                    raise Exception(f"OCR failed for {pdf_filename}")
            
            # If successful, break out of retry loop
            break
            
        except Exception as e:
            if retry < max_retries - 1:
                print(f"\nError processing {pdf_filename} (attempt {retry + 1}/{max_retries}): {e}")
                print("Retrying...")
                time.sleep(5)  # Wait before retry
            else:
                print(f"\nFailed to process {pdf_filename} after {max_retries} attempts: {e}")