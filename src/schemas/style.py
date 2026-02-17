from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class StylePresetRead(BaseModel):
    slug: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
