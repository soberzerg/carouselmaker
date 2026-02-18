from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class TextPosition(StrEnum):
    CENTER = "center"
    BOTTOM = "bottom"
    NONE = "none"


class SlideType(StrEnum):
    HOOK = "hook"
    CONTENT = "content"
    CTA = "cta"


class SlideContent(BaseModel):
    """AI-generated slide content."""

    position: int
    heading: str
    subtitle: str = ""
    body_text: str = ""
    text_position: TextPosition = TextPosition.NONE
    slide_type: SlideType = SlideType.CONTENT
    image_description: str = ""


class SlideRead(BaseModel):
    id: int
    carousel_id: int
    position: int
    heading: str
    subtitle: str = ""
    body_text: str = ""
    text_position: TextPosition = TextPosition.NONE
    slide_type: SlideType = SlideType.CONTENT
    image_s3_key: str | None = None
    rendered_s3_key: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
