from __future__ import annotations

from sam3.model_builder import download_ckpt_from_hf


if __name__ == "__main__":
    path = download_ckpt_from_hf(version="sam3.1")
    print(path)
