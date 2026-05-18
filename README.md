# Interactive Comic Generator

This project is an Entity Pool based interactive multi-panel comic generation system.

Phase one runs fully in mock mode. Phase two adds configurable real providers while keeping the same API and mock fallback:

- Qwen for lightweight text planning.
- OpenAI-compatible text provider as fallback.
- GPT Image for anchor and panel image generation.
- SAM 3.1 endpoint for entity segmentation.
- Mock providers remain available through `USE_MOCK_PROVIDERS=true`.

## Structure

- `backend/`: FastAPI service, provider layer, and comic generation pipeline.
- `frontend/`: Next.js / React application.
- `backend/outputs/{comic_id}/`: generated storyboard, entity pool, panels, reference sheets, entity refs, and final comic page.

## Backend

```bash
cd comic_project/backend
conda env create -f ../environment.yml
conda activate manhua
uvicorn main:app --reload --port 8000
```

If the environment already exists:

```bash
cd comic_project
conda env update -f environment.yml --prune
conda activate manhua
```

Main endpoints:

- `POST /api/comics`
- `GET /api/comics/{comic_id}/status`
- `GET /api/comics/{comic_id}`
- `POST /api/comics/{comic_id}/revise-global`
- `POST /api/comics/{comic_id}/revise-panel`

## Frontend

```bash
cd comic_project/frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend defaults to `http://localhost:8000` for the backend. To override it:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## Server Deployment

For a server, use real public URLs instead of localhost:

```bash
cd comic_project
export NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.example
export CORS_ORIGINS=https://your-frontend-domain.example
docker compose up --build
```

`NEXT_PUBLIC_API_BASE_URL` is embedded into the Next.js browser bundle at build time, so set it before building the frontend image. The backend serves generated files from `/outputs`, and `docker-compose.yml` persists them through `./backend/outputs:/app/outputs`.

To enable real providers:

```bash
cp .env.example .env
export USE_MOCK_PROVIDERS=false
export QWEN_API_KEY=...
export QWEN_BASE_URL=...
export QWEN_MODEL=...
export OPENAI_TEXT_API_KEY=...
export OPENAI_TEXT_BASE_URL=...
export OPENAI_TEXT_MODEL=...
export OPENAI_IMAGE_API_KEY=...
export OPENAI_IMAGE_BASE_URL=...
export OPENAI_IMAGE_MODEL=...
export SAM3_ENDPOINT=http://127.0.0.1:8100/segment
```

If Qwen fails, the backend tries OpenAI text, then mock text. If SAM3 fails, it falls back to mock segmentation and records a warning. If GPT Image fails, it falls back to mock images only when `ALLOW_MOCK_IMAGE_FALLBACK=true`; otherwise the API returns a clear error.

SAM 3.1 runs as a separate service in `sam3_service/`. On the server:

```bash
cp .env.example .env
cd comic_project/sam3_service
conda activate manhua
pip install "torch>=2.7" "torchvision>=0.22" --index-url https://download.pytorch.org/whl/cu126
pip install --upgrade "git+https://github.com/facebookresearch/sam3.git"
huggingface-cli login
uvicorn app:app --host 0.0.0.0 --port 8100
```

## Workflow

1. Enter a story description.
2. Choose a layout and style.
3. Click `Generate Comic`.
4. View `final_comic.png`, individual panels, reference sheets, provider status, warnings, and the Entity Pool sidebar.
5. Use `Apply Global Revision` to regenerate the back half of the comic.
6. Select one panel and use `Regenerate This Panel` to update only that panel.

The Entity Pool stores appearance history. Each entity starts with an anchor ref, then every generated or regenerated panel appends a new appearance ref.
