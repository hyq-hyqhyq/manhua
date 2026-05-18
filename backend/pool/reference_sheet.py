from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from image.anchor_generator import safe_text


def generate_reference_sheet(
    path: Path,
    panel_id: int,
    selected_refs: dict[str, list[dict]],
    public_to_disk_path,
) -> None:
    row_height = 210
    label_width = 170
    cell_width = 190
    rows = max(1, len(selected_refs))
    width = label_width + cell_width * 3 + 40
    height = 70 + rows * row_height

    image = Image.new("RGBA", (width, height), (248, 248, 244, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.rectangle((0, 0, width, 54), fill=(35, 35, 35, 255))
    draw.text((18, 18), safe_text(f"Reference Sheet - Panel {panel_id}"), fill=(255, 255, 255), font=font)

    for row_index, (entity_id, refs) in enumerate(selected_refs.items()):
        y = 70 + row_index * row_height
        draw.rectangle((14, y - 8, width - 14, y + row_height - 20), outline=(210, 210, 200), width=2)
        draw.text((24, y + 76), safe_text(entity_id), fill=(35, 35, 35), font=font)

        for ref_index, ref in enumerate(refs[:3]):
            x = label_width + ref_index * cell_width
            box = (x, y, x + 154, y + 154)
            try:
                ref_image = Image.open(public_to_disk_path(ref["rgba_path"])).convert("RGBA")
                ref_image.thumbnail((140, 140))
                paste_x = x + 7 + (140 - ref_image.width) // 2
                paste_y = y + 7 + (140 - ref_image.height) // 2
                draw.rectangle(box, fill=(255, 255, 255, 255), outline=(190, 190, 184), width=1)
                image.alpha_composite(ref_image, (paste_x, paste_y))
            except FileNotFoundError:
                draw.rectangle(box, fill=(235, 235, 235, 255), outline=(190, 190, 184), width=1)
                draw.text((x + 20, y + 65), safe_text("missing ref"), fill=(90, 90, 90), font=font)

            draw.text((x, y + 162), safe_text(ref["ref_id"]), fill=(40, 40, 40), font=font)
            draw.text((x, y + 178), safe_text(ref["source"]), fill=(90, 90, 90), font=font)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
