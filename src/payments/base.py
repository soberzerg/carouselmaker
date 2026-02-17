from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PaymentProvider(ABC):
    @abstractmethod
    async def create_payment(self, user_id: int, amount_rub: int, credit_amount: int) -> str:
        """Create a payment and return payment URL."""
        ...

    @abstractmethod
    async def verify_webhook(
        self, payload: dict[str, Any], signature: str
    ) -> dict[str, Any] | None:
        """Verify webhook signature. Returns parsed payload on success, None on failure."""
        ...
