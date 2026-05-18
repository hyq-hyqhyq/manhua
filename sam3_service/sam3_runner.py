from __future__ import annotations

from contextlib import nullcontext
import io
import threading
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageFilter

from config import settings


class SAM31Runner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loaded = False
        self._model = None
        self._processor = None
        self._loaded_version = ""

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def loaded_version(self) -> str:
        return self._loaded_version

    def segment(
        self,
        image_bytes: bytes,
        entity_id: str,
        description: str,
        prompt: str | None = None,
        score_threshold: float | None = None,
    ) -> bytes:
        self._ensure_loaded()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        prompt_text = self._build_prompt(entity_id, description, prompt)
        threshold = settings.score_threshold if score_threshold is None else score_threshold

        with torch.inference_mode(), self._autocast_context():
            state = self._processor.set_image(image.convert("RGB"))
            output = self._processor.set_text_prompt(state=state, prompt=prompt_text)

        mask = self._select_mask(output, threshold)
        cutout = self._apply_mask(image, mask)
        buffer = io.BytesIO()
        cutout.save(buffer, format="PNG")
        return buffer.getvalue()

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load_model()
            self._loaded = True

    def _load_model(self) -> None:
        from sam3.model.sam3_image_processor import Sam3Processor
        from sam3.model_builder import build_sam3_image_model, download_ckpt_from_hf

        checkpoint_path = settings.checkpoint_path or None
        load_from_hf = checkpoint_path is None

        if settings.version == "sam3.1" and checkpoint_path is None:
            checkpoint_path = download_ckpt_from_hf(version="sam3.1")
            load_from_hf = False

        try:
            model = build_sam3_image_model(
                checkpoint_path=checkpoint_path,
                load_from_HF=load_from_hf,
                device=settings.device,
                compile=settings.compile_model,
            )
            self._loaded_version = settings.version
        except Exception:
            if settings.version != "sam3.1" or not settings.allow_sam3_fallback:
                raise
            model = build_sam3_image_model(
                checkpoint_path=None,
                load_from_HF=True,
                device=settings.device,
                compile=settings.compile_model,
            )
            self._loaded_version = "sam3"

        self._model = model
        self._model.eval()
        self._processor = Sam3Processor(model)

    def _autocast_context(self):
        if not settings.device.startswith("cuda"):
            return nullcontext()
        if settings.dtype in {"bfloat16", "bf16"}:
            return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if settings.dtype in {"float16", "fp16"}:
            return torch.autocast(device_type="cuda", dtype=torch.float16)
        return nullcontext()

    def _build_prompt(self, entity_id: str, description: str, explicit_prompt: str | None) -> str:
        if explicit_prompt and explicit_prompt.strip():
            text = explicit_prompt.strip()
        elif settings.prompt_mode == "entity_id":
            text = entity_id
        elif settings.prompt_mode == "description":
            text = description or entity_id
        else:
            text = f"{entity_id}, {description}" if description else entity_id

        text = " ".join(text.split())
        return text[: settings.max_prompt_chars]

    def _select_mask(self, output: dict, score_threshold: float) -> np.ndarray:
        masks = output.get("masks")
        scores = output.get("scores")
        if masks is None:
            raise ValueError("SAM3 output did not contain masks")

        masks_np = self._to_numpy(masks)
        if masks_np.ndim == 4:
            masks_np = masks_np[:, 0]
        if masks_np.ndim == 2:
            masks_np = masks_np[None, :, :]
        if masks_np.size == 0 or masks_np.shape[0] == 0:
            raise ValueError("SAM3 returned no masks")

        scores_np = self._to_numpy(scores) if scores is not None else np.ones((masks_np.shape[0],))
        scores_np = np.asarray(scores_np).reshape(-1)
        if scores_np.size < masks_np.shape[0]:
            scores_np = np.pad(scores_np, (0, masks_np.shape[0] - scores_np.size), constant_values=0)

        binary_masks = masks_np > 0
        areas = binary_masks.reshape(binary_masks.shape[0], -1).sum(axis=1)
        valid = np.where((scores_np[: binary_masks.shape[0]] >= score_threshold) & (areas > 0))[0]
        if valid.size == 0:
            valid = np.where(areas > 0)[0]
        if valid.size == 0:
            raise ValueError("SAM3 masks were empty")

        image_area = binary_masks.shape[1] * binary_masks.shape[2]
        area_ratio = areas / max(1, image_area)
        area_penalty = np.where(area_ratio > 0.85, -0.25, 0.0)
        ranking = scores_np[: binary_masks.shape[0]] + area_penalty
        best_index = int(valid[np.argmax(ranking[valid])])
        return binary_masks[best_index].astype(np.uint8) * 255

    def _apply_mask(self, image: Image.Image, mask: np.ndarray) -> Image.Image:
        alpha = Image.fromarray(mask, mode="L").resize(image.size, Image.Resampling.NEAREST)
        if settings.alpha_blur_radius > 0:
            alpha = alpha.filter(ImageFilter.GaussianBlur(settings.alpha_blur_radius))
        output = image.copy()
        output.putalpha(alpha)
        return output

    def _to_numpy(self, value) -> np.ndarray:
        if value is None:
            return np.array([])
        if isinstance(value, torch.Tensor):
            return value.detach().float().cpu().numpy()
        if isinstance(value, list):
            return np.asarray([
                item.detach().float().cpu().numpy() if isinstance(item, torch.Tensor) else item
                for item in value
            ])
        return np.asarray(value)


runner = SAM31Runner()
