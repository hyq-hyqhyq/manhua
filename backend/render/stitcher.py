from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import settings


def stitch_panels(layout: str, panel_paths: list[Path], output_path: Path) -> None:
    if layout not in settings.layouts:
        raise ValueError(f"Unsupported layout: {layout}")

    rows = settings.layouts[layout]["rows"]
    cols = settings.layouts[layout]["cols"]
    cell = 640
    gutter = 24
    title_height = 58
    width = cols * cell + (cols + 1) * gutter
    height = title_height + rows * cell + (rows + 1) * gutter

    page = Image.new("RGB", (width, height), (252, 250, 244))
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default()
    draw.rectangle((0, 0, width, title_height), fill=(32, 32, 32))
    draw.text((gutter, 22), f"Mock Comic Page - {layout}", fill=(255, 255, 255), font=font)

    for index, panel_path in enumerate(panel_paths):
        row = index // cols
        col = index % cols
        x = gutter + col * (cell + gutter)
        y = title_height + gutter + row * (cell + gutter)
        try:
            panel = Image.open(panel_path).convert("RGB")
        except FileNotFoundError:
            panel = Image.new("RGB", (cell, cell), (235, 235, 235))
            ImageDraw.Draw(panel).text((24, 24), f"Missing panel {index + 1}", fill=(80, 80, 80), font=font)
        panel = panel.resize((cell, cell))
        page.paste(panel, (x, y))
        draw.rectangle((x, y, x + cell, y + cell), outline=(20, 20, 20), width=4)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path)
