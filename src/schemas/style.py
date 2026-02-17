from __future__ import annotations

from pydantic import BaseModel


class StylePresetRead(BaseModel):
    slug: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}
