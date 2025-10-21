
import os
from typing import Optional, AsyncGenerator, List

import modal
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse

from PIL import Image

from persistent_engine import stream_infer_image, infer_pdf_bytes_using_wrappers, get_async_engine, is_engine_ready

# Configuration
MODEL_REPO = "https://github.com/YuvrajSingh-mist/DeepSeek-OCR.git"
PYTORCH_INDEX = "https://download.pytorch.org/whl/cu118"
VLLM_WHEEL_NAME = "vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl"
WHEEL_URL = "https://github.com/vllm-project/vllm/releases/download/v0.8.5/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl"

# Use Python 3.9 in the image to match the vLLM wheel (cp38) used below.
IMAGE = modal.Image.from_registry("nvidia/cuda:11.8.0-devel-ubuntu22.04", add_python="3.9")

def build_image(image: modal.Image):
    # Build step: install PyTorch cu118, the vLLM wheel and dependencies from repo
    image = image.run_commands(
        "apt-get update && apt-get install -y git wget ca-certificates",
        f"git clone {MODEL_REPO} repo || true",
        "cd repo && pip install -r requirements.txt",
    )

    # Install PyTorch with CUDA 11.8
    image = image.uv_pip_install([
        "torch==2.6.0",
        "torchvision==0.21.0",
        "torchaudio==2.6.0",
    ], extra_options=f"--index-url {PYTORCH_INDEX}")

    # Install vLLM wheel
    if WHEEL_URL:
        image = image.uv_pip_install(WHEEL_URL)
    else:
        image = image.uv_pip_install(VLLM_WHEEL_NAME)

    # Install FastAPI and uvicorn
    image = image.uv_pip_install(["fastapi", "uvicorn[standard]"])

    # Install wheel for build dependencies
    image = image.uv_pip_install("wheel")

    # Install flash-attn
    image = image.uv_pip_install(["flash-attn==2.7.3"], extra_options="--no-build-isolation")

    return image

IMAGE = build_image(IMAGE)

# Create volumes for caches
hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("vllm-cache", create_if_missing=True)
volumes = {"/root/.cache/huggingface": hf_cache, "/root/.cache/vllm": vllm_cache}

app = modal.App("deepseek-ocr-modal", image=IMAGE)

fastapi_app = FastAPI(title='DeepSeek-OCR (Modal compatible)')


@fastapi_app.get('/health')
async def health():
    # Report whether the shared async engine is initialized (pre-warmed).
    ready = is_engine_ready()
    return JSONResponse({'ready': ready})


@fastapi_app.on_event('startup')
async def startup_event():
    # Try to pre-warm the shared engine so the first request is faster.
    try:
        get_async_engine()
    except Exception:
        # Do not crash startup here; health endpoint will reflect not-ready.
        pass


@fastapi_app.post('/upload/image')
async def upload_image(file: UploadFile = File(...), prompt: Optional[str] = None):
    """Accept an image upload and stream OCR output incrementally.

    Clients can stream the response to receive partial updates as the model
    generates text. We read the uploaded bytes into a PIL Image and call the
    persistent engine's async streaming generator.
    """
    contents = await file.read()
    try:
        img = Image.open(io := __import__('io').BytesIO(contents))
        img = img.convert('RGB')
    except Exception as e:
        return JSONResponse({'error': f'Invalid image file: {e}'}, status_code=400)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in stream_infer_image(img, prompt=prompt):
                # forward text chunks as bytes
                yield chunk.encode('utf-8')
        except Exception as e:
            yield f"ERROR: {e}".encode('utf-8')

    return StreamingResponse(event_stream(), media_type='text/plain')


@fastapi_app.post('/upload/pdf')
async def upload_pdf(file: UploadFile = File(...), prompt: Optional[str] = None):
    """Accept a PDF upload and stream per-page OCR outputs as NDJSON lines.

    Each line is a JSON object: {"page": <page_index>, "text": "..."}
    The endpoint yields one line per page as soon as that page's generation
    finishes. This allows clients to process pages progressively.
    """
    contents = await file.read()
    import tempfile
    import json

    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tf:
            tf.write(contents)
            tmp_pdf = tf.name

        try:
            from run_dpsk_ocr_pdf import pdf_to_images_high_quality  # type: ignore
        except Exception as e:
            return JSONResponse({'error': f'PDF helper import failed: {e}'}, status_code=500)

        images = pdf_to_images_high_quality(tmp_pdf)

        async def page_stream():
            # For each page, use the shared engine via persistent_engine.stream_infer_image
            for idx, img in enumerate(images):
                try:
                    page_chunks: List[str] = []
                    async for chunk in stream_infer_image(img, prompt=prompt):
                        if chunk:
                            page_chunks.append(chunk)

                    page_text = ''.join(page_chunks)
                    yield (json.dumps({"page": idx, "text": page_text}) + '\n').encode('utf-8')
                except Exception as e:
                    yield (json.dumps({"page": idx, "error": str(e)}) + '\n').encode('utf-8')

        return StreamingResponse(page_stream(), media_type='application/x-ndjson')

    finally:
        try:
            os.remove(tmp_pdf)
        except Exception:
            pass


@app.function(gpu="a100", volumes=volumes, timeout=30 * 60)
@modal.fastapi_endpoint()
def serve():
    # Clone the repo into the container and start uvicorn for the FastAPI app
    os.system(f"git clone {MODEL_REPO} repo || true")
    os.chdir("repo")
    # Ensure PROMPT env and MODEL_PATH are set if needed
    os.environ.setdefault("PROMPT", "<image>\n<|grounding|>Convert the document to markdown.")
    
    # Return the ASGI app object to Modal so the platform runs it with
    # its managed server (uvicorn is installed in the image during build).
    return fastapi_app

