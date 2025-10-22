
import os
from typing import Optional, AsyncGenerator, List
import io
import re
from concurrent.futures import ThreadPoolExecutor

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
MODEL_PATH = "deepseek-ai/DeepSeek-OCR"
DEFAULT_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."


def ensure_repo_and_paths():
    repo_dir = os.path.join(REPO_DIR, "DeepSeek-OCR")
    try:
        if not os.path.exists(repo_dir):
            # clone to /tmp then move
            subprocess.run(["git", "clone", "https://github.com/YuvrajSingh-mist/DeepSeek-OCR", "DeepSeek-OCR"], cwd="/tmp", check=True)
            subprocess.run(["mv", "/tmp/DeepSeek-OCR", repo_dir], check=True)
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

    # Install requirements from repo
    image = image.uv_pip_install([
        "transformers==4.46.3",
        "tokenizers==0.20.3",
        "PyMuPDF",
        "img2pdf",
        "einops",
        "easydict",
        "addict",
        "Pillow",
        "numpy",
        "tqdm"
    ])

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


# Class-based Modal function that keeps the model warm
@app.cls(
    gpu="A100-80GB",
    volumes=volumes,
    timeout=30 * 60,
    scaledown_window=600,  # Keep container alive for 10 minutes after last request
)
class DeepSeekOCRModel:
    """
    Persistent OCR model that initializes once and handles multiple requests.
    This avoids cold starts on every request by keeping the vLLM engine loaded in GPU memory.
    """
    
    @modal.enter()
    def initialize(self):
        """Initialize the model once when the container starts."""
        print("🚀 Initializing DeepSeek OCR model...")
        
        # Set environment variables
        os.environ["VLLM_USE_V1"] = "0"
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        
        # Ensure repo is available
        try:
            ensure_repo_and_paths()
        except Exception as e:
            print(f"Warning during repo setup: {e}")
        
        # Add vllm directory to path
        script_dir = os.path.join(REPO_DIR, "DeepSeek-OCR", "DeepSeek-OCR-master", "DeepSeek-OCR-vllm")
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        
        # Import required modules
        from deepseek_ocr import DeepseekOCRForCausalLM
        from vllm.model_executor.models.registry import ModelRegistry
        from vllm import LLM, SamplingParams
        from process.ngram_norepeat import NoRepeatNGramLogitsProcessor
        from process.image_process import DeepseekOCRProcessor
        import fitz  # PyMuPDF
        
        # Store imports as instance variables
        self.DeepseekOCRProcessor = DeepseekOCRProcessor
        self.fitz = fitz
        
        # Register model
        ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)
        
        # Initialize LLM engine
        print("📦 Loading vLLM engine...")
        self.llm = LLM(
            model=MODEL_PATH,
            hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
            block_size=256,
            enforce_eager=False,
            trust_remote_code=True,
            max_model_len=8192,
            swap_space=0,
            max_num_seqs=256,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            disable_mm_preprocessor_cache=True
        )
        
        # Setup logits processors
        logits_processors = [
            NoRepeatNGramLogitsProcessor(
                ngram_size=20,
                window_size=50,
                whitelist_token_ids={128821, 128822}  # <td>, </td>
            )
        ]
        
        # Setup sampling parameters
        self.sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            logits_processors=logits_processors,
            skip_special_tokens=False,
            include_stop_str_in_output=True,
        )
        
        print("✅ Model initialization complete!")
    
    def _pdf_to_images(self, pdf_bytes: bytes, dpi: int = 144) -> List[Image.Image]:
        """Convert PDF bytes to list of PIL Images."""
        images = []
        pdf_document = self.fitz.open(stream=pdf_bytes, filetype="pdf")
        
        zoom = dpi / 72.0
        matrix = self.fitz.Matrix(zoom, zoom)
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            images.append(img)
        
        pdf_document.close()
        return images
    
    def _process_single_image(self, image: Image.Image, prompt: str, crop_mode: bool = True):
        """Process a single image and return the cache item for vLLM."""
        processor = self.DeepseekOCRProcessor()
        cache_item = {
            "prompt": prompt,
            "multi_modal_data": {
                "image": processor.tokenize_with_images(
                    images=[image],
                    bos=True,
                    eos=True,
                    cropping=crop_mode
                )
            },
        }
        return cache_item
    
    @modal.method()
    def process_pdf(self, pdf_bytes: bytes, prompt: Optional[str] = None, skip_repeat: bool = True) -> dict:
        """
        Process a PDF file and return OCR results.
        
        Args:
            pdf_bytes: PDF file as bytes
            prompt: Optional custom prompt (defaults to markdown conversion)
            skip_repeat: Skip pages that don't have proper EOS token (likely repeated output)
        
        Returns:
            Dictionary with 'pages' (list of OCR text per page) and 'full_text' (combined)
        """
        print(f"📄 Processing PDF...")
        
        if prompt is None:
            prompt = DEFAULT_PROMPT
        
        # Convert PDF to images
        images = self._pdf_to_images(pdf_bytes)
        print(f"📸 Converted PDF to {len(images)} images")
        
        # Prepare batch inputs with ThreadPoolExecutor for faster preprocessing
        print("🔧 Preprocessing images...")
        with ThreadPoolExecutor(max_workers=min(64, len(images))) as executor:
            batch_inputs = list(executor.map(
                lambda img: self._process_single_image(img, prompt),
                images
            ))
        
        # Run inference
        print("🧠 Running OCR inference...")
        outputs_list = self.llm.generate(batch_inputs, sampling_params=self.sampling_params)
        
        # Process outputs
        pages = []
        for idx, output in enumerate(outputs_list):
            content = output.outputs[0].text
            
            # Check for proper EOS token
            if '<｜end▁of▁sentence｜>' in content:
                content = content.replace('<｜end▁of▁sentence｜>', '')
            else:
                if skip_repeat:
                    print(f"⚠️  Skipping page {idx + 1} (no EOS token - likely repeated output)")
                    continue
            
            # Clean up grounding tokens for markdown output
            content = self._clean_grounding_tokens(content)
            pages.append(content)
        
        print(f"✅ Processed {len(pages)} pages successfully")
        
        return {
            "pages": pages,
            "full_text": "\n\n<--- Page Split --->\n\n".join(pages),
            "num_pages": len(images),
            "num_successful": len(pages)
        }
    
    def _clean_grounding_tokens(self, content: str) -> str:
        """Remove grounding tokens from content."""
        # Pattern for grounding tokens: <|ref|>...<|/ref|><|det|>...<|/det|>
        pattern = r'<\|ref\|>.*?<\|/ref\|><\|det\|>.*?<\|/det\|>'
        content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Clean up LaTeX edge cases and extra newlines
        content = content.replace('\\coloneqq', ':=')
        content = content.replace('\\eqqcolon', '=:')
        content = re.sub(r'\n{4,}', '\n\n', content)
        
        return content


# FastAPI app for HTTP endpoints
fastapi_app = FastAPI(title='DeepSeek-OCR (Modal compatible)')


@fastapi_app.post('/repo/reset')
async def reset_repo():
    """Force clean and re-clone the repository."""
    repo_dir = os.path.join(REPO_DIR, "DeepSeek-OCR")
    if os.path.exists(repo_dir):
        subprocess.run(["rm", "-rf", repo_dir], check=True)
    # Clone to /tmp then move
    subprocess.run(["git", "clone", "https://github.com/YuvrajSingh-mist/DeepSeek-OCR", "DeepSeek-OCR"], cwd="/tmp", check=True)
    subprocess.run(["mv", "/tmp/DeepSeek-OCR", repo_dir], check=True)
    return {"status": "repo reset and cloned"}


@fastapi_app.post('/run/pdf')
async def run_pdf_endpoint(file: UploadFile = File(...)):
    """
    Process a PDF file using the warm OCR model.
    This endpoint now uses the persistent model instead of spawning subprocesses.
    """
    pdf_bytes = await file.read()
    
    # Call the Modal method (this will use the warm model)
    model = DeepSeekOCRModel()
    result = model.process_pdf.remote(pdf_bytes)
    
    return JSONResponse({
        "ocr_text": result["full_text"],
        "pages": result["pages"],
        "num_pages": result["num_pages"],
        "num_successful": result["num_successful"]
    })


@fastapi_app.get('/health')
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "model": "DeepSeek-OCR"}


@app.function(volumes=volumes, timeout=30 * 60)
@modal.asgi_app()
def serve():
    """Serve the FastAPI application."""
    # Ensure the mounted repo volume has the latest code and use it
    try:
        ensure_repo_and_paths()
    except Exception:
        # continue and let imports or startup report errors
        pass
    
    return fastapi_app

