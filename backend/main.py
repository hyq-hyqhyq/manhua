from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.comics import router as comics_router
from config import settings


settings.outputs_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Mock Comic Generator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    settings.static_outputs_prefix,
    StaticFiles(directory=settings.outputs_dir),
    name="outputs",
)

app.include_router(comics_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
