from pathlib import Path

from PIL import Image


def ensure_rgba_cutout(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    image.save(path)
