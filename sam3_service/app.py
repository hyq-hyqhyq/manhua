from __future__ import annotations

import traceback

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from config import settings
from sam3_runner import runner


app = FastAPI(title="SAM 3.1 Segmentation Service", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "loaded": runner.loaded,
        "configured_version": settings.version,
        "loaded_version": runner.loaded_version,
        "device": settings.device,
    }


@app.post("/segment")
async def segment(
    image: UploadFile = File(...),
    entity_id: str = Form(...),
    description: str = Form(""),
    prompt: str = Form(""),
    score_threshold: float | None = Form(None),
) -> Response:
    try:
        image_bytes = await image.read()
        output = runner.segment(
            image_bytes=image_bytes,
            entity_id=entity_id,
            description=description,
            prompt=prompt or None,
            score_threshold=score_threshold,
        )
        return Response(content=output, media_type="image/png")
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(error)) from error


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
