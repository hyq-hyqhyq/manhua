from pathlib import Path
from math import ceil, sqrt

from PIL import Image


CELL_SIZE = 512
MAX_REFS_PER_ENTITY = 3
BACKGROUND = (255, 255, 255, 255)


def generate_reference_sheet(
    path: Path,
    panel_id: int,
    selected_refs: dict[str, list[dict]],
    public_to_disk_path,
) -> None:
    rows = [
        refs[:MAX_REFS_PER_ENTITY]
        for refs in selected_refs.values()
    ]
    if not rows:
        rows = [[]]

    if len(rows) == 1:
        count = max(1, len(rows[0]))
        col_count = max(1, ceil(sqrt(count)))
        row_count = max(1, ceil(count / col_count))
        positions = [
            (index // col_count, index % col_count, ref)
            for index, ref in enumerate(rows[0])
        ]
    else:
        row_count = len(rows)
        col_count = max(1, max((len(refs) for refs in rows), default=1))
        positions = [
            (row_index, ref_index, ref)
            for row_index, refs in enumerate(rows)
            for ref_index, ref in enumerate(refs)
        ]

    side_cells = max(row_count, col_count)
    side = side_cells * CELL_SIZE
    image = Image.new("RGBA", (side, side), BACKGROUND)

    for row_index, ref_index, ref in positions:
        x = ref_index * CELL_SIZE
        y = row_index * CELL_SIZE
        try:
            ref_image = Image.open(public_to_disk_path(ref["rgba_path"])).convert("RGBA")
        except FileNotFoundError:
            continue

        ref_image.thumbnail((CELL_SIZE, CELL_SIZE), Image.Resampling.LANCZOS)
        paste_x = x + (CELL_SIZE - ref_image.width) // 2
        paste_y = y + (CELL_SIZE - ref_image.height) // 2
        image.alpha_composite(ref_image, (paste_x, paste_y))

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
