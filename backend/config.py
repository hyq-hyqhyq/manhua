from dataclasses import dataclass, field
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR.parent / ".env")
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


@dataclass(frozen=True)
class Settings:
    outputs_dir: Path = env_path("OUTPUT_DIR", BASE_DIR / "outputs")
    static_outputs_prefix: str = "/outputs"
    use_mock_providers: bool = env_bool("USE_MOCK_PROVIDERS", True)
    allow_mock_image_fallback: bool = env_bool("ALLOW_MOCK_IMAGE_FALLBACK", True)
    allow_mock_text_fallback: bool = env_bool("ALLOW_MOCK_TEXT_FALLBACK", True)
    allow_mock_segment_fallback: bool = env_bool("ALLOW_MOCK_SEGMENT_FALLBACK", True)
    request_timeout_seconds: float = float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "120"))
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_base_url: str = os.getenv("QWEN_BASE_URL", "")
    qwen_model: str = os.getenv("QWEN_MODEL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    openai_text_api_key: str = os.getenv(
        "OPENAI_TEXT_API_KEY", os.getenv("OPENAI_API_KEY", "")
    )
    openai_text_base_url: str = os.getenv(
        "OPENAI_TEXT_BASE_URL", os.getenv("OPENAI_BASE_URL", "")
    )
    openai_text_model: str = os.getenv("OPENAI_TEXT_MODEL", "")
    openai_image_api_key: str = os.getenv(
        "OPENAI_IMAGE_API_KEY", os.getenv("OPENAI_API_KEY", "")
    )
    openai_image_model: str = os.getenv("OPENAI_IMAGE_MODEL", "")
    openai_image_base_url: str = os.getenv("OPENAI_IMAGE_BASE_URL", "")
    openai_image_edits_endpoint: str = os.getenv("OPENAI_IMAGE_EDITS_ENDPOINT", "")
    openai_image_generations_endpoint: str = os.getenv(
        "OPENAI_IMAGE_GENERATIONS_ENDPOINT", ""
    )
    openai_image_endpoint: str = os.getenv("OPENAI_IMAGE_ENDPOINT", "")
    openai_image_timeout_seconds: float = float(
        os.getenv("OPENAI_IMAGE_TIMEOUT_SECONDS", "600")
    )
    sam3_endpoint: str = os.getenv("SAM3_ENDPOINT", "")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    )
    layouts: dict[str, dict[str, int]] = field(
        default_factory=lambda: {
            "1x4": {"rows": 4, "cols": 1, "panel_count": 4},
            "2x2": {"rows": 2, "cols": 2, "panel_count": 4},
            "2x3": {"rows": 2, "cols": 3, "panel_count": 6},
            "3x3": {"rows": 3, "cols": 3, "panel_count": 9},
        }
    )
    styles: tuple[str, ...] = (
        "black_white_manga",
        "color_webtoon",
        "american_comic",
        "children_book",
        "cinematic_comic",
    )
    style_prompts: dict[str, str] = field(
        default_factory=lambda: {
            "black_white_manga": (
                "black-and-white Japanese manga style, crisp ink lines, screen tones, "
                "dramatic composition"
            ),
            "color_webtoon": (
                "color webtoon style, clean digital line art, vibrant but controlled colors, "
                "expressive characters"
            ),
            "american_comic": (
                "American comic book style, bold outlines, dynamic poses, clear color blocks, "
                "cinematic action framing"
            ),
            "children_book": (
                "children's picture book style, warm shapes, gentle texture, readable silhouettes, "
                "friendly expressions"
            ),
            "cinematic_comic": (
                "cinematic comic style, filmic lighting, controlled contrast, atmospheric framing, "
                "storyboard clarity"
            ),
        }
    )


settings = Settings()
