
import os
from typing import Optional, AsyncGenerator, List

import modal
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse

from PIL import Image

import sys
import subprocess
import asyncio

# Configuration (must be defined before repository operations)
MODEL_REPO = os.environ.get("MODEL_REPO", "https://github.com/YuvrajSingh-mist/DeepSeek-OCR")
PYTORCH_INDEX = os.environ.get("PYTORCH_INDEX", "https://download.pytorch.org/whl/cu118")
VLLM_WHEEL_NAME = os.environ.get("VLLM_WHEEL_NAME", "vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl")
WHEEL_URL = os.environ.get("WHEEL_URL", "https://github.com/vllm-project/vllm/releases/download/v0.8.5/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl")

# Keep repository path simple and writable inside container
REPO_DIR = "/root/repo"


def ensure_repo_and_paths():
    repo_dir = os.path.join(REPO_DIR, "DeepSeek-OCR")
    try:
        if not os.path.exists(repo_dir):
            # clone to /tmp then move
            subprocess.run(["git", "clone", "https://github.com/YuvrajSingh-mist/DeepSeek-OCR", "DeepSeek-OCR"], cwd="/tmp", check=True)
            subprocess.run(["mv", "/tmp/DeepSeek-OCR", repo_dir], check=True)
            # Install requirements
            subprocess.run(["pip", "install", "-r", "requirements.txt"], cwd=repo_dir, check=True)
        else:
            # fetch latest changes
            subprocess.run(["git", "-C", repo_dir, "pull"], check=True)
    except Exception as e:
        # do not crash import — log and continue; later imports may fail if modules missing
        print(f"Warning: repo clone/pull failed: {e}")

    # Add repository directories to sys.path so modules like `persistent_engine` are importable
    repo_model_infra = os.path.join(repo_dir, "model_infra")
    if os.path.isdir(repo_model_infra) and repo_model_infra not in sys.path:
        sys.path.insert(0, repo_model_infra)

    if REPO_DIR not in sys.path:
        sys.path.insert(0, REPO_DIR)



# Placeholders for repo-provided functions; populated at startup
stream_infer_image = None
infer_pdf_bytes_using_wrappers = None
get_async_engine = None
is_engine_ready = lambda: False

# Global flag to ensure engine is loaded only once
engine_loaded = False


# Use Python 3.9 in the image to match the vLLM wheel (cp38) used below.
IMAGE = modal.Image.from_registry("nvidia/cuda:11.8.0-devel-ubuntu22.04", add_python="3.9")

def build_image(image: modal.Image):
    # Build step: install PyTorch cu118, the vLLM wheel and dependencies from repo
    image = image.run_commands(
        "apt-get update && apt-get install -y git wget ca-certificates",
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
    # if repo_present:
    #     try:
    #         repo_commit = subprocess.check_output(["git", "-C", REPO_DIR, "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
    #         repo_commit = repo_commit.decode().strip()
    #     except Exception:
    #         repo_commit = None

    modules_loaded = {
        'stream_infer_image': stream_infer_image is not None,
        'infer_pdf_bytes_using_wrappers': infer_pdf_bytes_using_wrappers is not None,
        'get_async_engine': get_async_engine is not None,
    }

    return JSONResponse({'ready': ready, 'repo_present': repo_present, 'repo_commit': repo_commit, 'modules_loaded': modules_loaded})


@fastapi_app.post('/repo/reset')
async def reset_repo():
    """Force clean and re-clone the repository."""
    repo_dir = os.path.join(REPO_DIR, "DeepSeek-OCR")
    if os.path.exists(repo_dir):
        subprocess.run(["rm", "-rf", repo_dir], check=True)
    # Clone to /tmp then move
    subprocess.run(["git", "clone", "https://github.com/YuvrajSingh-mist/DeepSeek-OCR", "DeepSeek-OCR"], cwd="/tmp", check=True)
    subprocess.run(["mv", "/tmp/DeepSeek-OCR", repo_dir], check=True)
    # Install requirements
    subprocess.run(["pip", "install", "-r", "requirements.txt"], cwd=repo_dir, check=True)
    return {"status": "repo reset and cloned"}


@fastapi_app.post('/run/pdf')
async def run_pdf_script(file: UploadFile = File(...)):
    """Run the run_dpsk_ocr_pdf.py script on the uploaded PDF file and stream the output."""
    contents = await file.read()
    
    # Save the uploaded file to /tmp
    input_file = '/tmp/input.pdf'
    with open(input_file, 'wb') as f:
        f.write(contents)
    
    # Path to the script
    script_dir = os.path.join(REPO_DIR, "DeepSeek-OCR", "DeepSeek-OCR-master", "DeepSeek-OCR-vllm")
    script_path = os.path.join(script_dir, "run_dpsk_ocr_pdf.py")
    
    # Run the script with args and stream stdout
    process = await asyncio.create_subprocess_exec(
        "python", script_path, "--input", input_file, "--output", script_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=script_dir
    )
    
    async def stream_output():
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line
    
    return StreamingResponse(stream_output(), media_type='text/plain')


@app.function(gpu="A100-80GB", volumes=volumes, timeout=30 * 60)
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
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    
    return fastapi_app

