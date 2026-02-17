from __future__ import annotations

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credit_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    credit_transactions: Mapped[list[CreditTransaction]] = relationship(
        "CreditTransaction", back_populates="user", lazy="selectin"
    )
    carousel_generations: Mapped[list[CarouselGeneration]] = relationship(
        "CarouselGeneration", back_populates="user", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id}>"


# Avoid circular imports — these are resolved at runtime by SQLAlchemy string refs
from src.models.carousel import CarouselGeneration  # noqa: E402, F401
from src.models.credit import CreditTransaction  # noqa: E402, F401
