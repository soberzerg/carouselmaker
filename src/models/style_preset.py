from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class StylePreset(TimestampMixin, Base):
    __tablename__ = "style_presets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    config_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<StylePreset slug={self.slug}>"
