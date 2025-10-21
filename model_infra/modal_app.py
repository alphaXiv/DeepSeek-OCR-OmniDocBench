
import os
from typing import Optional, AsyncGenerator, List

import modal
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse

from PIL import Image

import sys
import subprocess

# Configuration (must be defined before repository operations)
MODEL_REPO = os.environ.get("MODEL_REPO", "https://github.com/YuvrajSingh-mist/DeepSeek-OCR.git")
PYTORCH_INDEX = os.environ.get("PYTORCH_INDEX", "https://download.pytorch.org/whl/cu118")
VLLM_WHEEL_NAME = os.environ.get("VLLM_WHEEL_NAME", "vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl")
WHEEL_URL = os.environ.get("WHEEL_URL", "https://github.com/vllm-project/vllm/releases/download/v0.8.5/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl")

# Keep repository path simple and writable inside container
REPO_DIR = "/root/repo"


def ensure_repo_and_paths():
    try:
        if not os.path.exists(REPO_DIR):
            # shallow clone to reduce transfer time
            subprocess.run(["git", "clone", "--depth", "1", MODEL_REPO, REPO_DIR], check=True)
        else:
            # fetch latest changes
            subprocess.run(["git", "-C", MODEL_REPO, "pull"], check=True)
    except Exception as e:
        # do not crash import — log and continue; later imports may fail if modules missing
        print(f"Warning: repo clone/pull failed: {e}")

    # Add repository directories to sys.path so modules like `persistent_engine` are importable
    repo_model_infra = os.path.join(REPO_DIR, "model_infra")
    if os.path.isdir(repo_model_infra) and repo_model_infra not in sys.path:
        sys.path.insert(0, repo_model_infra)

    if REPO_DIR not in sys.path:
        sys.path.insert(0, REPO_DIR)



# Placeholders for repo-provided functions; populated at startup
stream_infer_image = None
infer_pdf_bytes_using_wrappers = None
get_async_engine = None
is_engine_ready = lambda: False


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
repo_volume = modal.Volume.from_name("deepseek-ocr-repo", create_if_missing=True)
volumes = {
    "/root/.cache/huggingface": hf_cache,
    "/root/.cache/vllm": vllm_cache,
    "/root/repo": repo_volume,
}

app = modal.App("deepseek-ocr-modal", image=IMAGE)

fastapi_app = FastAPI(title='DeepSeek-OCR (Modal compatible)')
# @fastapi_app.get('/health')

@fastapi_app.get('/health')
async def health():
    # Report whether the shared async engine is initialized (pre-warmed).
    ready = False
    try:
        ready = bool(callable(get_async_engine) and is_engine_ready())
    except Exception:
        ready = False

    # Repo diagnostics
    repo_present = os.path.isdir(REPO_DIR)
    repo_commit = None
    if repo_present:
        try:
            repo_commit = subprocess.check_output(["git", "-C", REPO_DIR, "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
            repo_commit = repo_commit.decode().strip()
        except Exception:
            repo_commit = None

    modules_loaded = {
        'stream_infer_image': stream_infer_image is not None,
        'infer_pdf_bytes_using_wrappers': infer_pdf_bytes_using_wrappers is not None,
        'get_async_engine': get_async_engine is not None,
    }

    return JSONResponse({'ready': ready, 'repo_present': repo_present, 'repo_commit': repo_commit, 'modules_loaded': modules_loaded})


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    try:
        ensure_repo_and_paths()
    except Exception as e:
        print(f"Warning: repo clone/pull failed during startup: {e}")

    # Import repo-backed helpers now that volumes are mounted
    global stream_infer_image, infer_pdf_bytes_using_wrappers, get_async_engine, is_engine_ready
    try:
        # Add repo path (already added in ensure_repo_and_paths) to sys.path
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)
        from persistent_engine import stream_infer_image as _sii, infer_pdf_bytes_using_wrappers as _ipw, get_async_engine as _gae, is_engine_ready as _ier
        stream_infer_image = _sii
        infer_pdf_bytes_using_wrappers = _ipw
        get_async_engine = _gae
        is_engine_ready = _ier
    except Exception as e:
        print(f"Error importing persistent repo modules on startup: {e}")

    try:
        if callable(get_async_engine):
            get_async_engine()
    except Exception:
        # Do not crash startup here; health endpoint will reflect not-ready.
        pass

    # Log registered FastAPI routes for debugging
    try:
        routes_info = []
        for r in app.routes:
            # route may be Starlette Route or APIRoute
            try:
                path = r.path
                methods = getattr(r, 'methods', None)
            except Exception:
                path = str(r)
                methods = None
            routes_info.append({'path': path, 'methods': list(methods) if methods else None})
        print("FastAPI routes:", routes_info)
    except Exception as e:
        print("Failed to enumerate FastAPI routes:", e)

    yield

    # Shutdown code (if needed)

fastapi_app = FastAPI(lifespan=lifespan)


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
@modal.asgi_app()
def serve():
    # Ensure the mounted repo volume has the latest code and use it
    try:
        ensure_repo_and_paths()
    except Exception:
        # continue and let imports or startup report errors
        pass
    os.chdir(REPO_DIR)
    # Ensure PROMPT env and MODEL_PATH are set if needed
    os.environ.setdefault("PROMPT", "<image>\n<|grounding|>Convert the document to markdown.")
    
    return fastapi_app

