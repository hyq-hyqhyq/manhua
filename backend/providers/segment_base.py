from abc import ABC, abstractmethod
from pathlib import Path


class SegmentProvider(ABC):
    provider_name = "segment"

    @abstractmethod
    def segment_entity(
        self,
        image_path: Path,
        entity_id: str,
        description: str,
        output_path: Path,
    ) -> None:
        raise NotImplementedError
