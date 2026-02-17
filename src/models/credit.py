from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User


class TransactionType(enum.StrEnum):
    WELCOME_BONUS = "welcome_bonus"
    PURCHASE = "purchase"
    GENERATION_CHARGE = "generation_charge"
    REFUND = "refund"
    ADMIN_GRANT = "admin_grant"


class CreditTransaction(TimestampMixin, Base):
    __tablename__ = "credit_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"), nullable=False
    )
    external_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="credit_transactions")

    def __repr__(self) -> str:
        return f"<CreditTransaction id={self.id} amount={self.amount} type={self.transaction_type}>"
