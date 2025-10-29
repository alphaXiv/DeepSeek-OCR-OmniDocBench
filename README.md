# DeepSeek-OCR vs OLMOCR-2 Evaluation on OmniDocBench

This repository provides a comparative evaluation of **DeepSeek-OCR** and **OLMOCR-2** on the **OmniDocBench** benchmark. The evaluation assesses document parsing capabilities across text, formulas, tables, and reading order.

## Overview

- **DeepSeek-OCR**: A vLLM-based multimodal pipeline for document understanding.
- **OLMOCR-2**: An efficient OCR system using open visual language models.
- **OmniDocBench**: A comprehensive benchmark with 1,355 annotated PDF pages covering diverse document types.

## Setup

### 1. OmniDocBench Setup
Follow the setup instructions in [`OmniDocBench/README.md`](OmniDocBench/README.md).



### 2. OLMOCR Setup
Follow the setup instructions in [`olmocr/README.md`](olmocr/README.md).


### 3. DeepSeek-OCR Setup
Follow the installation guide in [`DeepSeek-OCR-master/README.md`](DeepSeek-OCR-master/README.md).

## Get the data

We used the HuggingFace version and based all our evals on it.

Can be found at [link](https://huggingface.co/datasets/opendatalab/OmniDocBench)


For olmOCR2, convert the images to PDFs using the following

```bash

python utils/image_to_pdf.py

```

Our outputs can be found in the 'markdown_olmo_ocr_2' folder.


## Running the Models

### Generate Outputs from DeepSeek-OCR

1. Navigate to the DeepSeek-OCR directory:
   ```bash
   cd DeepSeek-OCR-master/DeepSeek-OCR-vllm
   ```

2. Configure paths in `config.py`:
   - Set `INPUT_PATH` to the OmniDocBench images directory (e.g., `../../OmniDocBench/images/`)
   - Set `OUTPUT_PATH` to a directory for output .md files (e.g., `../../outputs/deepseek_ocr/`)

3. Run inference on images:
   ```bash
   python run_dpsk_ocr_eval_batch.py
   ```

   This will process all images and generate corresponding `.md` files in the output directory. Remember to use 'cleaned' .md files for evaluation, which can be found in `./tools/cleaned_markdown/` that we generated.

### Generate Outputs from OLMOCR-2

1. Navigate to the olmocr directory:
   ```bash
   cd olmocr
   ```

2. Run inference on PDFs:
   ```bash
   python -m olmocr.pipeline ./localworkspace --markdown --pdfs tests/gnarly_pdfs/*.pdf
   ```

   Replace `tests/gnarly_pdfs/` with a workspace directory, that includes your pdf files.

   The `--markdown` flag ensures `.md` files are generated in the workspace's `markdown/` subdirectory.

## Evaluation

Use OmniDocBench's evaluation scripts to compare the generated outputs.

### End-to-End Evaluation (md2md)

1. Configure `OmniDocBench/configs/md2md.yaml`:
   - Set `ground_truth.data_path` to `OmniDocBench/OmniDocBench.json`
   - Set `ground_truth.page_info` to `OmniDocBench/OmniDocBench.json`
   - Set `prediction.data_path` to the directory containing model outputs (e.g., `outputs/deepseek_ocr/` or `olmocr_workspace/markdown/`)

2. Run evaluation:
   ```bash
   cd OmniDocBench
   python pdf_validation.py --config configs/end2end.yaml
   ```


## Results

After evaluation, results are stored in `OmniDocBench/result/`. Use the notebooks in `OmniDocBench/tools/` to generate comparison tables and visualizations.

You can find our results in `results` folder too!

Key metrics include:
- Text accuracy (normalized edit distance)
- Formula accuracy (Edit dist score)
- Table TEDS score
- Reading order accuracy
- Overall score: ((1 - text_edit) × 100 + table_teds + (1 - edit_distance) × 100) / 3

## Comparison Summary

Based on the evaluation:
- DeepSeek-OCR achieves an overall accuracy of **84.24%**
- OLMOCR-2 achieves an overall accuracy of **81.56%**
- DeepSeek-OCR shows strengths in text and table recovery
- Both models perform well on reading order but have room for improvement in formula parsing

See [`REPORT.md`](REPORT.md) for detailed results and visualizations.

