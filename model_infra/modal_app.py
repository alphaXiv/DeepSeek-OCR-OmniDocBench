import os
from typing import Optional, AsyncGenerator, List
import io
import re
from concurrent.futures import ThreadPoolExecutor

import modal
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from PIL import Image
import sys
import subprocess
import asyncio
from PIL import ImageDraw, ImageFont, ImageOps
import numpy as np
import base64
import io as _io


# from config import MAX_CONCURRENCY

# Import metrics collector


# Configuration (must be defined before repository operations)
MODEL_REPO = os.environ.get("MODEL_REPO", "https://github.com/YuvrajSingh-mist/DeepSeek-OCR")
PYTORCH_INDEX = os.environ.get("PYTORCH_INDEX", "https://download.pytorch.org/whl/cu118")
VLLM_WHEEL_NAME = os.environ.get("VLLM_WHEEL_NAME", "vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl")
WHEEL_URL = os.environ.get("WHEEL_URL", "https://github.com/vllm-project/vllm/releases/download/v0.8.5/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl")

# Keep repository path simple and writable inside container
REPO_DIR = "/root/repo"
MODEL_PATH = "deepseek-ai/DeepSeek-OCR"
DEFAULT_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."



os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
        "tqdm",
        "aiohttp",
        "GPUtil",
        "psutil",
        "kaleido"
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

@app.cls(
    gpu="A100-80GB",
    volumes=volumes,
    timeout=30 * 60,
    scaledown_window=600,  # Keep container alive for 10 minutes after last request
    min_containers=2,
    max_containers=5
)
@modal.concurrent(max_inputs=16, target_inputs=8)
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
            gpu_memory_utilization=0.90,
            disable_mm_preprocessor_cache=True,
            dtype='bfloat16'
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
        # from metrics_collector import metrics_collector
        
        # Start metrics collection
        # with metrics_collector.collect_metrics():
        if prompt is None:
            prompt = DEFAULT_PROMPT
        
        # Convert PDF to images
        images = self._pdf_to_images(pdf_bytes)
        print(f"📸 Converted PDF to {len(images)} images")

        # Process images in batches to reduce GPU memory pressure and control concurrency
        # Default batch size chosen to balance throughput and memory; it's safe to tune.
        batch_size = 32
        pages = []

        print("🔧 Preprocessing + inference in batches...")
        for start in range(0, len(images), batch_size):
            chunk = images[start : start + batch_size]

            # Tokenize / preprocess this chunk in parallel (keeps work on GPU-side code paths)
            with ThreadPoolExecutor(max_workers=min(64, len(chunk))) as executor:
                batch_inputs = list(executor.map(lambda img: self._process_single_image(img, prompt), chunk))

            # Run inference for this chunk
            print(f"🧠 Running OCR inference for pages {start + 1}..{start + len(chunk)}")
            outputs_chunk = self.llm.generate(batch_inputs, sampling_params=self.sampling_params)

            # Process outputs for this chunk and append
            for j, output in enumerate(outputs_chunk):
                idx = start + j
                content = output.outputs[0].text
    
                # Check for proper EOS token
                if "<｜end▁of▁sentence｜>" in content:
                    content = content.replace("<｜end▁of▁sentence｜>", "")
                else:
                    if skip_repeat:
                        print(f"⚠️  Skipping page {idx + 1} (no EOS token - likely repeated output)")
                        continue

                # Clean up grounding tokens for markdown output
                content = self._clean_grounding_tokens(content)
                pages.append(content)
        
        print(f"✅ Processed {len(pages)} pages successfully")
        
        # Get final metrics
        # final_metrics = metrics_collector.get_last_metrics()
        
        result = {
            "pages": pages,
            "full_text": "\n\n<--- Page Split --->\n\n".join(pages),
            "num_pages": len(images),
            "num_successful": len(pages)
        }
        
        # # Add performance metrics to result
        # if final_metrics:
        #     result["performance_metrics"] = {
        #         "duration_seconds": round(final_metrics.duration, 3),
        #         "gpu_memory_peak_mb": round(final_metrics.gpu_memory_peak, 2),
        #         "gpu_utilization_avg_percent": round(final_metrics.gpu_utilization_avg, 2),
        #         "cpu_usage_avg_percent": round(final_metrics.cpu_usage_avg, 2),
        #         "gpu_metrics_samples": len(final_metrics.gpu_metrics_history)
        #     }
        
        return result
    
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

    # --- Image-specific helpers ported from run_dpsk_ocr_image.py (adapted to in-memory outputs) ---
    def _re_match(self, text: str):
        pattern = r'(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)'
        matches = re.findall(pattern, text, re.DOTALL)

        mathes_image = []
        mathes_other = []
        for a_match in matches:
            if '<|ref|>image<|/ref|>' in a_match[0]:
                mathes_image.append(a_match[0])
            else:
                mathes_other.append(a_match[0])
        return matches, mathes_image, mathes_other

    def _extract_coordinates_and_label(self, ref_text, image_width, image_height):
        try:
            label_type = ref_text[1]
            cor_list = eval(ref_text[2])
        except Exception as e:
            print(e)
            return None

        return (label_type, cor_list)

    def _draw_bounding_boxes(self, image: Image.Image, refs):
        """Draw boxes and return (annotated_image, list_of_cropped_images).
        Cropped images are returned as PIL.Image objects (not saved to disk).
        """
        image_width, image_height = image.size
        img_draw = image.copy()
        draw = ImageDraw.Draw(img_draw)

        overlay = Image.new('RGBA', img_draw.size, (0, 0, 0, 0))
        draw2 = ImageDraw.Draw(overlay)
        font = ImageFont.load_default()

        img_idx = 0
        crops = []
        for i, ref in enumerate(refs):
            try:
                result = self._extract_coordinates_and_label(ref, image_width, image_height)
                if result:
                    label_type, points_list = result
                    color = (np.random.randint(0, 200), np.random.randint(0, 200), np.random.randint(0, 255))
                    color_a = color + (20,)
                    for points in points_list:
                        x1, y1, x2, y2 = points
                        x1 = int(x1 / 999 * image_width)
                        y1 = int(y1 / 999 * image_height)
                        x2 = int(x2 / 999 * image_width)
                        y2 = int(y2 / 999 * image_height)

                        if label_type == 'image':
                            try:
                                cropped = image.crop((x1, y1, x2, y2))
                                crops.append(cropped)
                            except Exception as e:
                                print(e)
                                pass
                            img_idx += 1

                        try:
                            if label_type == 'title':
                                draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
                                draw2.rectangle([x1, y1, x2, y2], fill=color_a, outline=(0, 0, 0, 0), width=1)
                            else:
                                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                                draw2.rectangle([x1, y1, x2, y2], fill=color_a, outline=(0, 0, 0, 0), width=1)

                            text_x = x1
                            text_y = max(0, y1 - 15)
                            text_bbox = draw.textbbox((0, 0), label_type, font=font)
                            text_width = text_bbox[2] - text_bbox[0]
                            text_height = text_bbox[3] - text_bbox[1]
                            draw.rectangle([text_x, text_y, text_x + text_width, text_x + text_height],
                                           fill=(255, 255, 255, 30))
                            draw.text((text_x, text_y), label_type, font=font, fill=color)
                        except Exception:
                            pass
            except Exception:
                continue
        img_draw.paste(overlay, (0, 0), overlay)
        return img_draw, crops

    def _process_image_with_refs(self, image: Image.Image, ref_texts):
        annotated, crops = self._draw_bounding_boxes(image, ref_texts)
        return annotated, crops

    @modal.method()
    def process_image(self, image_bytes: bytes, prompt: Optional[str] = None, crop_mode: bool = True) -> dict:
        """
        Process a single image bytes and return OCR results along with annotated image and crops (base64).
        """
        if prompt is None:
            prompt = DEFAULT_PROMPT

        # Load image
        try:
            image = Image.open(_io.BytesIO(image_bytes))
            image = ImageOps.exif_transpose(image).convert('RGB')
        except Exception as e:
            return {"error": "invalid_image", "message": str(e)}

        # Create cache item like the PDF flow
        processor = self.DeepseekOCRProcessor()
        cache_item = {
            "prompt": prompt,
            "multi_modal_data": {
                "image": processor.tokenize_with_images(images=[image], bos=True, eos=True, cropping=crop_mode)
            },
        } #Its fine since only one image per req will be handled anyways so no batching :)

        outputs = list(self.llm.generate([cache_item], sampling_params=self.sampling_params))
        if not outputs:
            return {"error": "no_output"}

        content = outputs[0].outputs[0].text

        # Post-process content
        if "<｜end▁of▁sentence｜>" in content:
            content = content.replace("<｜end▁of▁sentence｜>", "")

        matches_ref, matches_images, mathes_other = self._re_match(content)

        # Replace image refs and other grounding refs in content; do NOT save or return images
        for idx, a_match_image in enumerate(matches_images):
            # replace image refs with a simple placeholder or remove them
            content = content.replace(a_match_image, f'')

        for idx, a_match_other in enumerate(mathes_other):
            content = content.replace(a_match_other, '').replace('\\coloneqq', ':=').replace('\\eqqcolon', '=:')

        return {
            "raw_output": outputs[0].outputs[0].text,
            "full_text": content,
        }


# FastAPI app for HTTP endpoints
fastapi_app = FastAPI(title='DeepSeek-OCR (Modal compatible)')

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or restrict to specific domains)
    allow_credentials=False,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


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
    Process a PDF file using the app modal implementation (batched processing).
    This endpoint uses the persistent model instance.
    """
    import fitz
    
    pdf_bytes = await file.read()
    
    # Verify the file is a valid PDF by attempting to open it
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        pdf_document.close()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid file format",
                "message": "The uploaded file is not a valid PDF"
            }
        )


    max_size = 64 * 1024 * 1024  
    if len(pdf_bytes) > max_size:
        return JSONResponse(
            status_code=413,
            content={
                "error": "File too large",
                "message": f"Maximum file size is 64MB. Uploaded file is {len(pdf_bytes) / (1024*1024):.1f}MB"
            }
        )
    
    # Check page count limit (150 pages)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = pdf_document.page_count
    pdf_document.close()
    if num_pages > 150:
        return JSONResponse(
            status_code=413,
            content={
                "error": "Too many pages",
                "message": f"Maximum number of pages is 150. PDF has {num_pages} pages"
            }
        )
    
    # Call the Modal method (this will use the warm model)
    model = DeepSeekOCRModel()
    result = model.process_pdf.remote(pdf_bytes)
    
    return JSONResponse({
        "implementation": "app",
        "ocr_text": result["full_text"],
        "pages": result["pages"],
        "num_pages": result["num_pages"],
        "num_successful": result["num_successful"],
        "performance_metrics": result.get("performance_metrics", {})
    })


@fastapi_app.post('/run/image')
async def run_image_endpoint(file: UploadFile = File(...)):
    """
    Process a single image using the persistent model instance.
    Returns OCR text and annotated image / crops as base64 strings.
    """
    image_bytes = await file.read()

    # Basic size guard
    max_size = 16 * 1024 * 1024
    if len(image_bytes) > max_size:
        return JSONResponse(status_code=413, content={"error": "file too large", "message": "Max 16MB"})

    model = DeepSeekOCRModel()
    result = model.process_image.remote(image_bytes)

    if "error" in result:
        return JSONResponse(status_code=400, content=result)

    # Return only text results (no images)
    return JSONResponse({
        "implementation": "app",
        "ocr_text": result.get("full_text", ""),
        "raw_output": result.get("raw_output", ""),
    })


@fastapi_app.get('/health')
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "model": "DeepSeek-OCR"}


@app.function(volumes=volumes, timeout=30 * 60, min_containers=2, max_containers=5, scaledown_window=600)
@modal.asgi_app()
@modal.concurrent(max_inputs=32, target_inputs=16)
def serve():
    """Serve the FastAPI application."""
    # Ensure the mounted repo volume has the latest code and use it
    try:
        ensure_repo_and_paths()
    except Exception:
        # continue and let imports or startup report errors
        pass
    
    return fastapi_app