import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class FileStore:
    def __init__(self, outputs_dir: Path, public_prefix: str = "/outputs"):
        self.outputs_dir = outputs_dir
        self.public_prefix = public_prefix.rstrip("/")
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def create_comic_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"comic_{timestamp}_{uuid4().hex[:8]}"

    def init_comic_dir(self, comic_id: str) -> Path:
        comic_dir = self.comic_dir(comic_id)
        for child in ("anchors", "panels", "reference_sheets", "entity_pool"):
            (comic_dir / child).mkdir(parents=True, exist_ok=True)
        return comic_dir

    def comic_dir(self, comic_id: str) -> Path:
        return self.outputs_dir / comic_id

    def require_comic_dir(self, comic_id: str) -> Path:
        comic_dir = self.comic_dir(comic_id)
        if not comic_dir.exists():
            raise FileNotFoundError(f"Comic not found: {comic_id}")
        return comic_dir

    def save_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_json(self, path: Path) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def to_public_path(self, path: Path) -> str:
        relative = path.resolve().relative_to(self.outputs_dir.resolve())
        return f"{self.public_prefix}/{relative.as_posix()}"

    def public_to_disk_path(self, public_path: str) -> Path:
        normalized = public_path.strip()
        if normalized.startswith(self.public_prefix + "/"):
            normalized = normalized[len(self.public_prefix) + 1 :]
        elif normalized.startswith("outputs/"):
            normalized = normalized[len("outputs/") :]
        return self.outputs_dir / normalized
