from __future__ import annotations

from pydantic import BaseModel


class SlideContent(BaseModel):
    """AI-generated slide content."""

    position: int
    heading: str
    body_text: str


class SlideRead(BaseModel):
    id: int
    carousel_id: int
    position: int
    heading: str
    body_text: str
    image_s3_key: str | None = None
    rendered_s3_key: str | None = None

    model_config = {"from_attributes": True}
