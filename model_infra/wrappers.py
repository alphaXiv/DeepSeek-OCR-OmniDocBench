"""Lightweight wrappers that reuse DeepSeek-OCR vllm scripts to run inference.

These functions import the image/pdf processing and the async stream generator from
the repository's vllm scripts and provide sync wrappers that return text outputs.
"""
import sys
import os
import io
import asyncio
from typing import Optional, List

# Ensure the repo vllm package is importable when this module is executed from
# a different working directory (for example inside Modal container).
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VLLM_DIR = os.path.join(REPO_ROOT, 'DeepSeek-OCR-master', 'DeepSeek-OCR-vllm')
if VLLM_DIR not in sys.path:
    sys.path.insert(0, VLLM_DIR)

from PIL import Image, ImageOps

# Defer importing repo specific modules to runtime inside the functions. This
# keeps static analysis from failing when the repo modules are not on sys.path
# at analysis time.


def _ensure_pil_image(image_bytes: bytes) -> Image.Image:
    bio = io.BytesIO(image_bytes)
    im = Image.open(bio)
    try:
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    return im.convert('RGB')


def ocr_image_bytes(image_bytes: bytes, prompt: Optional[str] = None) -> str:
    """Run OCR on a single image (bytes). Returns the final text output string.

    This reuses the repo's DeepseekOCRProcessor to tokenize the image and then
    calls the async stream_generate function provided by the repo.
    """
    from PIL import ImageOps
    im = _ensure_pil_image(image_bytes)

    # Import repo-specific utilities at runtime
    try:
        from run_dpsk_ocr_image import stream_generate, DeepseekOCRProcessor  # type: ignore
    except Exception as e:
        raise RuntimeError("Failed to import run_dpsk_ocr_image from the repository. "
                           "Ensure working directory contains DeepSeek-OCR master folder and sys.path is set.") from e

    # The repo expects a tokenized image via DeepseekOCRProcessor
    processor = DeepseekOCRProcessor()
    image_features = processor.tokenize_with_images(images=[im], bos=True, eos=True, cropping=True)

    prompt = prompt or os.environ.get('PROMPT')
    if not prompt:
        # default fallback (matches repo README default)
        prompt = '<image>\n<|grounding|>Convert the document to markdown.'

    # stream_generate is async and yields incremental chunks; run it and collect
    final_chunks = []
    async def run_and_collect():
        async for chunk in stream_generate(image=image_features, prompt=prompt):
            # skip the final empty terminator chunk
            if chunk:
                final_chunks.append(chunk)

    asyncio.run(run_and_collect())
    return ''.join(final_chunks)


def ocr_pdf_bytes(pdf_bytes: bytes, prompt: Optional[str] = None) -> List[str]:
    """Run OCR on a PDF (bytes). Converts to images and runs per-page OCR.

    Returns a list of per-page outputs (strings). This is a simple wrapper that
    uses the repo's pdf helper to convert pdf->images and then calls the image
    wrapper for each page. For large PDFs consider batching.
    """
    try:
        from run_dpsk_ocr_pdf import pdf_to_images_high_quality  # type: ignore
        from run_dpsk_ocr_image import stream_generate, DeepseekOCRProcessor  # type: ignore
    except Exception as e:
        raise RuntimeError("Failed to import pdf/image helpers from repository. "
                           "Ensure the working directory contains the DeepSeek-OCR repo and sys.path is configured.") from e

    import tempfile

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tf:
        tf.write(pdf_bytes)
        tmp_pdf = tf.name

    images = pdf_to_images_high_quality(tmp_pdf)

    outputs = []
    for img in images:
        processor = DeepseekOCRProcessor()
        image_features = processor.tokenize_with_images(images=[img], bos=True, eos=True, cropping=True)
        final_chunks = []

        async def run_and_collect_page():
            async for chunk in stream_generate(image=image_features, prompt=prompt or os.environ.get('PROMPT')):
                if chunk:
                    final_chunks.append(chunk)

        asyncio.run(run_and_collect_page())
        outputs.append(''.join(final_chunks))

    try:
        os.remove(tmp_pdf)
    except Exception:
        pass

    return outputs
