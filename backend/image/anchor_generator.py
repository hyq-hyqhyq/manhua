from hashlib import sha256
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def color_for_text(text: str) -> tuple[int, int, int]:
    digest = sha256(text.encode("utf-8")).digest()
    return 80 + digest[0] % 140, 80 + digest[1] % 140, 80 + digest[2] % 140


def generate_anchor_ref_image(path: Path, entity_id: str, description: str, ref_id: str) -> None:
    image = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    color = color_for_text(entity_id)

    draw.rounded_rectangle((38, 26, 222, 226), radius=28, fill=(*color, 230), outline=(25, 25, 25, 255), width=3)
    draw.ellipse((82, 48, 178, 144), fill=(245, 235, 220, 255), outline=(30, 30, 30, 255), width=2)
    draw.rectangle((74, 140, 186, 218), fill=(*color, 255), outline=(30, 30, 30, 255), width=2)

    draw.text((18, 8), safe_text("ANCHOR"), fill=(20, 20, 20, 255), font=font)
    draw.text((58, 154), safe_text(entity_id), fill=(255, 255, 255, 255), font=font)
    draw.text((18, 232), safe_text(ref_id), fill=(20, 20, 20, 255), font=font)
    _draw_wrapped(draw, description, (18, 246), 34, font, fill=(30, 30, 30, 255))

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _draw_wrapped(draw, text: str, xy: tuple[int, int], limit: int, font, fill) -> None:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > limit and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)

    x, y = xy
    for line in lines[:1]:
        draw.text((x, y), safe_text(line), fill=fill, font=font)


def safe_text(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")
