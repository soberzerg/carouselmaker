from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.carousel import CarouselGeneration


class Slide(TimestampMixin, Base):
    __tablename__ = "slides"
    __table_args__ = (
        UniqueConstraint("carousel_id", "position", name="uq_slide_carousel_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    carousel_id: Mapped[int] = mapped_column(
        ForeignKey("carousel_generations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str] = mapped_column(String(500), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rendered_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    carousel: Mapped[CarouselGeneration] = relationship(
        "CarouselGeneration", back_populates="slides"
    )

    def __repr__(self) -> str:
        return f"<Slide id={self.id} pos={self.position}>"
