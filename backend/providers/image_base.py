from abc import ABC, abstractmethod
from pathlib import Path


class ImageProvider(ABC):
    provider_name = "image"

    @abstractmethod
    def generate_anchor_image(
        self,
        entity_id: str,
        description: str,
        style_prompt: str,
        output_path: Path,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def generate_panel_image(
        self,
        panel_prompt: str,
        reference_sheet_path: Path,
        output_path: Path,
    ) -> None:
        raise NotImplementedError
