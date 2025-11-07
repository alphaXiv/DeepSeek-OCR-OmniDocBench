"""Top-level minimal config shim.

This provides the small set of names that `model_infra/modal_app.py` imports:
MODEL_REPO, MODEL_PATH, DEFAULT_PROMPT, MAX_CONCURRENCY.

Keep this file minimal to avoid affecting other parts of the repo.
"""

import os

# Defaults (can be overridden with environment variables)
MODEL_REPO = os.environ.get("MODEL_REPO", "https://github.com/YuvrajSingh-mist/DeepSeek-OCR")
MODEL_PATH = os.environ.get("MODEL_PATH", "deepseek-ai/DeepSeek-OCR")
DEFAULT_PROMPT = os.environ.get("DEFAULT_PROMPT", "<image>\n<|grounding|>Convert the document to markdown.")
MAX_CONCURRENCY = int(os.environ.get("MAX_CONCURRENCY", "512"))

__all__ = ["MODEL_REPO", "MODEL_PATH", "DEFAULT_PROMPT", "MAX_CONCURRENCY"]
