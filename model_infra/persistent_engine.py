
import os
import sys
from typing import List, Optional

from PIL import Image

# Ensure the repo vllm folder is on sys.path so runtime imports succeed when
# the module is used inside the Modal image or local dev environment.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VLLM_DIR = os.path.join(REPO_ROOT, 'DeepSeek-OCR-master', 'DeepSeek-OCR-vllm')
if VLLM_DIR not in sys.path:
    sys.path.insert(0, VLLM_DIR)

# Lazy singleton for AsyncLLMEngine
_async_engine = None


def get_async_engine():
    """Lazily construct and return a shared AsyncLLMEngine instance."""
    global _async_engine
    if _async_engine is not None:
        return _async_engine

    try:
        from vllm import AsyncLLMEngine
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.model_executor.models.registry import ModelRegistry
        from deepseek_ocr import DeepseekOCRForCausalLM
        from config import MODEL_PATH
    except Exception as e:
        raise RuntimeError("Failed to import vLLM or repo modules required to create engine") from e

    try:
        ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)
    except Exception:
        pass

    engine_args = AsyncEngineArgs(
        model=MODEL_PATH,
        hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
        block_size=256,
        max_model_len=8192,
        enforce_eager=False,
        trust_remote_code=True,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.75,
    )

    _async_engine = AsyncLLMEngine.from_engine_args(engine_args)
    return _async_engine


def is_engine_ready() -> bool:
    return _async_engine is not None


async def stream_infer_image(image: Image.Image, prompt: Optional[str] = None):
    """Async generator that streams incremental outputs for a single image.

    Prefer using the shared AsyncLLMEngine created by `get_async_engine()` for
    lower latency on subsequent requests. If engine creation/import fails,
    fall back to the repository streaming generator.
    """
    prompt_text = prompt or os.environ.get('PROMPT') or '<image>\n<|grounding|>Convert the document to markdown.'

    # Tokenize image with the repo processor
    try:
        from process.image_process import DeepseekOCRProcessor  # type: ignore
    except Exception as e:
        raise RuntimeError("Failed to import DeepseekOCRProcessor from repo") from e

    processor = DeepseekOCRProcessor()
    image_features = processor.tokenize_with_images(images=[image], bos=True, eos=True, cropping=True)

    request = {"prompt": prompt_text, "multi_modal_data": {"image": image_features}}

    # Try the shared engine path
    try:
        engine = get_async_engine()

        from vllm import SamplingParams  # type: ignore
        from process.ngram_norepeat import NoRepeatNGramLogitsProcessor  # type: ignore

        logits_processors = [NoRepeatNGramLogitsProcessor(ngram_size=30, window_size=90, whitelist_token_ids={128821, 128822})]

        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            logits_processors=logits_processors,
            skip_special_tokens=False,
        )

        import time
        request_id = f"request-{int(time.time())}"

        printed_length = 0
        final_output = ''

        async for request_output in engine.generate(request, sampling_params, request_id):
            if request_output.outputs:
                full_text = request_output.outputs[0].text
                new_text = full_text[printed_length:]
                if new_text:
                    yield new_text
                printed_length = len(full_text)
                final_output = full_text

        if final_output:
            yield ''

        return
    except Exception:
        # Fallback to repo streaming generator
        try:
            from run_dpsk_ocr_image import stream_generate  # type: ignore
        except Exception as e:
            raise RuntimeError("Both shared engine and repo generator failed") from e

        async for chunk in stream_generate(image=image_features, prompt=prompt_text):
            yield chunk



def infer_image_bytes_using_wrappers(image_bytes: bytes, prompt: Optional[str] = None) -> str:
    try:
        from wrappers import ocr_image_bytes  # type: ignore
    except Exception as e:
        raise RuntimeError("Failed to import wrappers. Ensure repository path is correct.") from e

    return ocr_image_bytes(image_bytes=image_bytes, prompt=prompt)


def infer_pdf_bytes_using_wrappers(pdf_bytes: bytes, prompt: Optional[str] = None) -> List[str]:
    try:
        from wrappers import ocr_pdf_bytes  # type: ignore
    except Exception as e:
        raise RuntimeError("Failed to import wrappers. Ensure repository path is correct.") from e

    return ocr_pdf_bytes(pdf_bytes=pdf_bytes, prompt=prompt)
