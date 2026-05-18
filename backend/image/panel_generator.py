from hashlib import sha256
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont

from image.anchor_generator import color_for_text, safe_text


STYLE_PALETTES = {
    "black_white_manga": ((244, 244, 240), (35, 35, 35), (255, 255, 255)),
    "color_webtoon": ((235, 248, 245), (26, 72, 82), (255, 242, 153)),
    "american_comic": ((255, 246, 230), (40, 54, 120), (239, 74, 67)),
    "children_book": ((255, 250, 232), (85, 101, 67), (255, 184, 105)),
    "cinematic_comic": ((238, 241, 240), (30, 33, 34), (118, 139, 122)),
}


def generate_panel_image(
    path: Path,
    panel_id: int,
    summary: str,
    style: str,
    entities_used: list[str],
    selected_refs: dict[str, list[dict]],
    text_items: list[dict] | None = None,
) -> None:
    background, ink, accent = STYLE_PALETTES.get(style, STYLE_PALETTES["color_webtoon"])
    width, height = 768, 768
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.rectangle((18, 18, width - 18, height - 18), outline=ink, width=5)
    draw.rectangle((18, 18, width - 18, 92), fill=ink)
    draw.text((36, 42), safe_text(f"PANEL {panel_id}"), fill=background, font=font)
    draw.text((142, 42), safe_text(style), fill=accent, font=font)

    seed = int.from_bytes(sha256(f"{panel_id}:{summary}".encode("utf-8")).digest()[:2], "big")
    horizon = 250 + seed % 80
    draw.rectangle((48, horizon, width - 48, height - 120), outline=ink, width=3)
    draw.line((48, horizon + 60, width - 48, horizon + 25), fill=ink, width=2)

    entity_x = 110
    for entity_id in entities_used:
        color = color_for_text(entity_id)
        draw_entity(draw, entity_x, 340 + (seed % 30), color, entity_id, font, ink)
        entity_x += 210

    summary_lines = textwrap.wrap(summary, width=78)
    y = 112
    for line in summary_lines[:7]:
        draw.text((42, y), safe_text(line), fill=ink, font=font)
        y += 18

    if text_items:
        text_y = 242
        for item in text_items[:2]:
            label = item.get("type", "text")
            speaker = item.get("speaker")
            content = item.get("content", "")
            prefix = f"[{label}]"
            if speaker:
                prefix += f"[{speaker}]"
            line = safe_text(f"{prefix} {content}")
            draw.rounded_rectangle(
                (44, text_y, width - 44, text_y + 38),
                radius=14,
                fill=(255, 255, 255),
                outline=ink,
                width=2,
            )
            draw.text((62, text_y + 12), line, fill=ink, font=font)
            text_y += 48

    ref_y = height - 92
    draw.rectangle((36, ref_y - 16, width - 36, height - 36), outline=ink, width=2)
    draw.text((52, ref_y), safe_text("selected refs:"), fill=ink, font=font)
    ref_text = []
    for entity_id, refs in selected_refs.items():
        ref_text.append(f"{entity_id}({','.join(ref['ref_id'] for ref in refs)})")
    draw.text((52, ref_y + 18), safe_text(" | ".join(ref_text)[:100]), fill=ink, font=font)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def generate_entity_appearance_ref(
    path: Path,
    entity_id: str,
    ref_id: str,
    source: str,
    note: str,
) -> None:
    image = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    color = color_for_text(f"{entity_id}:{ref_id}")
    ink = (28, 28, 28, 255)

    draw.rounded_rectangle((40, 34, 220, 222), radius=22, fill=(*color, 225), outline=ink, width=3)
    draw.ellipse((86, 48, 174, 136), fill=(245, 234, 214, 255), outline=ink, width=2)
    draw.polygon([(72, 218), (188, 218), (166, 136), (94, 136)], fill=(*color, 255), outline=ink)
    draw.text((18, 12), safe_text(source), fill=ink, font=font)
    draw.text((72, 152), safe_text(entity_id), fill=(255, 255, 255, 255), font=font)
    draw.text((18, 230), safe_text(ref_id), fill=ink, font=font)
    draw.text((18, 246), safe_text(note[:36]), fill=ink, font=font)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def draw_entity(draw, x: int, y: int, color, label: str, font, ink) -> None:
    draw.ellipse((x + 26, y - 74, x + 102, y + 2), fill=(245, 235, 220), outline=ink, width=3)
    draw.rectangle((x, y, x + 130, y + 160), fill=color, outline=ink, width=3)
    draw.line((x + 22, y + 160, x - 10, y + 224), fill=ink, width=5)
    draw.line((x + 104, y + 160, x + 142, y + 224), fill=ink, width=5)
    draw.text((x + 18, y + 68), safe_text(label), fill=(255, 255, 255), font=font)
