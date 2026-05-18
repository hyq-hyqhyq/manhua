from typing import Any, Literal

from pydantic import BaseModel, Field


LayoutName = Literal["1x4", "2x2", "2x3", "3x3"]
StyleName = Literal[
    "black_white_manga",
    "color_webtoon",
    "american_comic",
    "children_book",
    "cinematic_comic",
]


class ComicCreateRequest(BaseModel):
    user_prompt: str = Field(..., min_length=1)
    layout: LayoutName
    style: StyleName


class RevisionRequest(BaseModel):
    feedback: str = Field(..., min_length=1)


TextType = Literal["speech", "thought", "caption", "sfx"]
TextPosition = Literal[
    "top_left",
    "top_center",
    "top_right",
    "middle_left",
    "middle_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
]


class PanelTextItem(BaseModel):
    type: TextType
    speaker: str | None = None
    content: str = Field(..., min_length=1)
    position: TextPosition


class PanelRevisionRequest(BaseModel):
    panel_id: int = Field(..., ge=1)
    feedback: str = ""
    summary: str | None = None
    text: list[PanelTextItem] | None = None


class ComicCreateResponse(BaseModel):
    comic_id: str
    status: str


class ComicStatusResponse(BaseModel):
    status: str
    current_panel: int
    total_panels: int
    message: str
    warnings: list[str] = Field(default_factory=list)
    provider_status: dict[str, str] = Field(default_factory=dict)


class RevisionResponse(BaseModel):
    comic_id: str
    status: str
    revision_plan: dict[str, Any]
