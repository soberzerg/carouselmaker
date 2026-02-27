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


class ContentTemplate(StrEnum):
    TEXT = "text"
    LISTING = "listing"
    COMPARISON = "comparison"


class ComparisonBlock(BaseModel):
    label: str
    items: list[str]


class ComparisonData(BaseModel):
    top_block: ComparisonBlock
    bottom_block: ComparisonBlock


class ListingData(BaseModel):
    items: list[str]


class SlideContent(BaseModel):
    """AI-generated slide content."""

    position: int
    heading: str
    subtitle: str = ""
    body_text: str = ""
    text_position: TextPosition = TextPosition.NONE
    slide_type: SlideType = SlideType.CONTENT
    image_description: str = ""
    content_template: ContentTemplate = ContentTemplate.TEXT
    listing_data: ListingData | None = None
    comparison_data: ComparisonData | None = None
    slide_number: int | None = None


class SlideRead(BaseModel):
    id: int
    carousel_id: int
    position: int
    heading: str
    subtitle: str = ""
    body_text: str = ""
    text_position: TextPosition = TextPosition.NONE
    slide_type: SlideType = SlideType.CONTENT
    content_template: ContentTemplate = ContentTemplate.TEXT
    image_s3_key: str | None = None
    rendered_s3_key: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
