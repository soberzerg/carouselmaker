from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from src.models.carousel import GenerationStatus


class CarouselGenerationCreate(BaseModel):
    input_text: str
    style_slug: str


class CarouselGenerationRead(BaseModel):
    id: int
    user_id: int
    input_text: str
    style_slug: str
    status: GenerationStatus
    slide_count: int | None = None
    celery_task_id: str | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
