from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User


class PaymentStatus(enum.StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    yookassa_payment_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    amount_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
    )

    user: Mapped[User] = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} yookassa={self.yookassa_payment_id} "
            f"status={self.status} amount={self.amount_rub}>"
        )
