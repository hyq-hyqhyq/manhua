# Backend

FastAPI backend for the interactive comic generator.

The backend supports mock mode and real provider mode:

- `USE_MOCK_PROVIDERS=true`: fully mock storyboard, images, and segmentation.
- `USE_MOCK_PROVIDERS=false`: OpenAI-compatible GPT text + GPT Image + SAM3 with fallback paths.

The phase-one API shape is preserved.

## Run

```bash
cd comic_project/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

For a server, set CORS to the real frontend origin:

```bash
CORS_ORIGINS=https://your-frontend-domain.example uvicorn main:app --host 0.0.0.0 --port 8000
```

## Provider Environment

```bash
USE_MOCK_PROVIDERS=false
ALLOW_MOCK_IMAGE_FALLBACK=true
ALLOW_MOCK_TEXT_FALLBACK=true
ALLOW_MOCK_SEGMENT_FALLBACK=true

OPENAI_TEXT_API_KEY=...
OPENAI_TEXT_BASE_URL=...
OPENAI_TEXT_MODEL=...
OPENAI_IMAGE_API_KEY=...
OPENAI_IMAGE_BASE_URL=...
OPENAI_IMAGE_MODEL=...
OPENAI_IMAGE_TIMEOUT_SECONDS=600
OPENAI_IMAGE_EDITS_ENDPOINT=/v1/images/edits
OPENAI_IMAGE_GENERATIONS_ENDPOINT=/v1/images/generations

SAM3_ENDPOINT=https://your-sam3-endpoint.example/segment
OUTPUT_DIR=outputs
```

Fallback behavior:

- OpenAI text failure: fallback to mock text when enabled.
- GPT Image failure: clear API error unless mock image fallback is enabled.
- SAM3 failure: fallback to mock cutout and record a warning.

Generated assets are saved in:

```text
outputs/{comic_id}/
  anchors/{entity_id}_anchor.png
  storyboard.json
  entity_pool.json
  panels/panel_1.png
  reference_sheets/panel_1_refsheet.png
  entity_pool/{entity_id}/{ref_id}.png
  final_comic.png
```

## API

Create:

```bash
curl -X POST http://localhost:8000/api/comics \
  -H "Content-Type: application/json" \
  -d '{"user_prompt":"A teenage boy in a blue raincoat meets a talking gray cat on a rainy night.","layout":"2x2","style":"black_white_manga"}'
```

Global revision:

```bash
curl -X POST http://localhost:8000/api/comics/{comic_id}/revise-global \
  -H "Content-Type: application/json" \
  -d '{"feedback":"Make the final panels more tense."}'
```

Panel revision:

```bash
curl -X POST http://localhost:8000/api/comics/{comic_id}/revise-panel \
  -H "Content-Type: application/json" \
  -d '{"panel_id":3,"feedback":"Move the hero closer to the camera."}'
```
