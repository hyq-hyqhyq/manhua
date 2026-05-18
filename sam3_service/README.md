# SAM 3.1 Segmentation Service

This is a standalone FastAPI service for the main comic backend.

The main backend calls:

```text
POST /segment
```

with:

- `image`: anchor or panel image.
- `entity_id`: short entity id, such as `boy` or `cat`.
- `description`: entity description from the storyboard.

The service returns a transparent PNG RGBA cutout.

## Why Separate

SAM 3.1 is heavy and GPU-oriented. Keeping it in a separate service lets the comic backend stay small while SAM 3.1 owns the GPU process.

Meta's official repo says SAM 3 requires Python 3.12+, PyTorch 2.7+, and CUDA 12.6+. SAM 3.1 checkpoints are hosted on Hugging Face at `facebook/sam3.1`, and access is gated, so you must accept the license and authenticate on the server.

Sources:

- https://github.com/facebookresearch/sam3
- https://huggingface.co/facebook/sam3.1

## Server Install

```bash
cd comic_project
conda env create -f environment.yml
conda activate manhua
pip install "torch>=2.7" "torchvision>=0.22" --index-url https://download.pytorch.org/whl/cu126
pip install --upgrade "git+https://github.com/facebookresearch/sam3.git"
```

Then authenticate Hugging Face:

```bash
huggingface-cli login
```

Optionally pre-download the checkpoint:

```bash
source .venv/bin/activate
python scripts/download_sam31.py
```

## Start

```bash
cd comic_project/sam3_service
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8100
```

Test:

```bash
curl http://127.0.0.1:8100/health
```

## Main Backend Config

In `comic_project/.env`:

```env
USE_MOCK_PROVIDERS=false
SAM3_ENDPOINT=http://127.0.0.1:8100/segment
ALLOW_MOCK_SEGMENT_FALLBACK=true
```

## Local Checkpoint

If you manually download a checkpoint, set:

```env
SAM3_CHECKPOINT_PATH=/absolute/path/to/sam3.1_multiplex.pt
```

The service defaults to:

```env
SAM3_VERSION=sam3.1
SAM3_DEVICE=cuda
SAM3_DTYPE=bfloat16
SAM3_PROMPT_MODE=entity_id
```
