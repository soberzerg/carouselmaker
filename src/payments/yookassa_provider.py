from __future__ import annotations

import logging

from src.payments.base import PaymentProvider

logger = logging.getLogger(__name__)


class YooKassaStubProvider(PaymentProvider):
    """Stub payment provider — immediately credits user without real payment."""

    async def create_payment(self, user_id: int, amount_rub: int, credit_amount: int) -> str:
        logger.info(
            "STUB: Payment created for user %d: %d RUB → %d credits",
            user_id, amount_rub, credit_amount,
        )
        # In real implementation, this would call YooKassa API and return payment URL
        return f"https://stub-payment.local/{user_id}/{amount_rub}"

    async def verify_webhook(self, payload: dict, signature: str) -> bool:
        logger.info("STUB: Webhook verification (always returns True)")
        return True
