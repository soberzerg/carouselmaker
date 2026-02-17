from __future__ import annotations

from abc import ABC, abstractmethod


class PaymentProvider(ABC):
    @abstractmethod
    async def create_payment(self, user_id: int, amount_rub: int, credit_amount: int) -> str:
        """Create a payment and return payment URL."""
        ...

    @abstractmethod
    async def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Verify webhook signature."""
        ...
