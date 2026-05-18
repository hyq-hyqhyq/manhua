#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3.12}"
VENV_DIR="${VENV_DIR:-.venv}"
TORCH_INDEX_URL="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu126}"

cd "$(dirname "$0")/.."

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
pip install "torch>=2.7" "torchvision>=0.22" --index-url "${TORCH_INDEX_URL}"
pip install -r requirements.txt
pip install --upgrade "git+https://github.com/facebookresearch/sam3.git"

cat <<'MSG'

SAM 3.1 service dependencies are installed.

Before first run, authenticate Hugging Face on this server:
  huggingface-cli login

Then start:
  source .venv/bin/activate
  uvicorn app:app --host 0.0.0.0 --port 8100

MSG
