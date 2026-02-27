from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PaymentResult:
    """Result of creating a payment via a payment provider."""

    url: str  # Confirmation URL for the user to pay
    external_id: str  # Payment ID from the external provider (e.g., YooKassa UUID)


class PaymentProvider(ABC):
    @abstractmethod
    async def create_payment(
        self, user_id: int, amount_rub: int, credit_amount: int
    ) -> PaymentResult:
        """Create a payment and return PaymentResult with URL and external ID."""
        ...

    @abstractmethod
    async def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """Fetch payment details from the provider API."""
        ...

    @abstractmethod
    async def verify_webhook(
        self, payload: dict[str, Any], signature: str
    ) -> dict[str, Any] | None:
        """Verify webhook payload. Returns parsed payment data on success, None on failure."""
        ...
