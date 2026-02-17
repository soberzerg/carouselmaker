from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class GenerationStatus(enum.StrEnum):
    PENDING = "pending"
    COPYWRITING = "copywriting"
    IMAGE_GENERATION = "image_generation"
    RENDERING = "rendering"
    UPLOADING = "uploading"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"


class CarouselGeneration(TimestampMixin, Base):
    __tablename__ = "carousel_generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    style_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, name="generation_status"),
        default=GenerationStatus.PENDING,
        nullable=False,
    )
    slide_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="carousel_generations")
    slides: Mapped[list[Slide]] = relationship(
        "Slide", back_populates="carousel", lazy="selectin", order_by="Slide.position"
    )

    def __repr__(self) -> str:
        return f"<CarouselGeneration id={self.id} status={self.status}>"


from src.models.slide import Slide  # noqa: E402, F401
from src.models.user import User  # noqa: E402, F401
