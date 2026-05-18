from fastapi import APIRouter, HTTPException

from pipeline.comic_pipeline import ComicPipeline
from schemas import (
    ComicCreateRequest,
    ComicCreateResponse,
    ComicStatusResponse,
    PanelRevisionRequest,
    RevisionRequest,
    RevisionResponse,
)


router = APIRouter(prefix="/api/comics", tags=["comics"])
pipeline = ComicPipeline()


def _as_http_error(error: Exception) -> HTTPException:
    if isinstance(error, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=500, detail=str(error))


@router.post("", response_model=ComicCreateResponse)
def create_comic(request: ComicCreateRequest) -> dict[str, str]:
    try:
        return pipeline.create_comic(
            user_prompt=request.user_prompt,
            layout=request.layout,
            style=request.style,
        )
    except Exception as error:
        raise _as_http_error(error) from error


@router.get("/{comic_id}/status", response_model=ComicStatusResponse)
def get_status(comic_id: str) -> dict:
    try:
        return pipeline.get_status(comic_id)
    except Exception as error:
        raise _as_http_error(error) from error


@router.get("/{comic_id}")
def get_comic(comic_id: str) -> dict:
    try:
        return pipeline.get_comic(comic_id)
    except Exception as error:
        raise _as_http_error(error) from error


@router.post("/{comic_id}/revise-global", response_model=RevisionResponse)
def revise_global(comic_id: str, request: RevisionRequest) -> dict:
    try:
        return pipeline.revise_global(comic_id, request.feedback)
    except Exception as error:
        raise _as_http_error(error) from error


@router.post("/{comic_id}/revise-panel", response_model=RevisionResponse)
def revise_panel(comic_id: str, request: PanelRevisionRequest) -> dict:
    try:
        return pipeline.revise_panel(comic_id, request.panel_id, request.feedback)
    except Exception as error:
        raise _as_http_error(error) from error
