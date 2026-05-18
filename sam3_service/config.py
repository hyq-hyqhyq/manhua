from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    SERVICE_DIR = Path(__file__).resolve().parent
    load_dotenv(SERVICE_DIR.parent / ".env")
    load_dotenv(SERVICE_DIR / ".env")
except ImportError:
    SERVICE_DIR = Path(__file__).resolve().parent


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("SAM3_SERVICE_HOST", "0.0.0.0")
    port: int = int(os.getenv("SAM3_SERVICE_PORT", "8100"))
    device: str = os.getenv("SAM3_DEVICE", "cuda")
    dtype: str = os.getenv("SAM3_DTYPE", "bfloat16")
    version: str = os.getenv("SAM3_VERSION", "sam3.1")
    image_version: str = os.getenv("SAM3_IMAGE_VERSION", "sam3")
    checkpoint_path: str = os.getenv("SAM3_CHECKPOINT_PATH", "")
    prompt_mode: str = os.getenv("SAM3_PROMPT_MODE", "combined")
    score_threshold: float = env_float("SAM3_SCORE_THRESHOLD", 0.15)
    max_prompt_chars: int = int(os.getenv("SAM3_MAX_PROMPT_CHARS", "120"))
    compile_model: bool = env_bool("SAM3_COMPILE", False)
    allow_sam3_fallback: bool = env_bool("SAM3_ALLOW_SAM3_FALLBACK", False)
    alpha_blur_radius: float = env_float("SAM3_ALPHA_BLUR_RADIUS", 0.0)


settings = Settings()
