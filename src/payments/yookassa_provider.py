from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx

from src.payments.base import PaymentProvider, PaymentResult

logger = logging.getLogger(__name__)


class YooKassaProvider(PaymentProvider):
    """Real YooKassa payment provider using their REST API v3."""

    BASE_URL = "https://api.yookassa.ru/v3"

    def __init__(
        self,
        shop_id: str,
        secret_key: str,
        return_url: str = "",
    ) -> None:
        self._shop_id = shop_id
        self._secret_key = secret_key
        self._return_url = return_url
        self._auth = (shop_id, secret_key)

    async def create_payment(
        self, user_id: int, amount_rub: int, credit_amount: int
    ) -> PaymentResult:
        """Create a payment via YooKassa API and return confirmation URL + payment ID.

        Uses HTTP Basic Auth (shop_id:secret_key) and an idempotence key (UUID4)
        to ensure safe retries.
        """
        idempotence_key = str(uuid.uuid4())

        payload: dict[str, Any] = {
            "amount": {
                "value": f"{amount_rub}.00",
                "currency": "RUB",
            },
            "capture": True,
            "description": f"{credit_amount} credits for Nano Banana Carousel Maker",
            "metadata": {
                "user_id": str(user_id),
                "credit_amount": str(credit_amount),
            },
        }

        if self._return_url:
            payload["confirmation"] = {
                "type": "redirect",
                "return_url": self._return_url,
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/payments",
                json=payload,
                auth=self._auth,
                headers={
                    "Idempotence-Key": idempotence_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

        if response.status_code != 200:
            logger.error(
                "YooKassa create_payment failed: status=%d body=%s",
                response.status_code,
                response.text,
            )
            msg = f"YooKassa API error: {response.status_code}"
            raise RuntimeError(msg)

        data = response.json()
        payment_id = data["id"]
        confirmation_url = data.get("confirmation", {}).get("confirmation_url", "")

        if not confirmation_url:
            logger.error("YooKassa response missing confirmation_url: %s", data)
            msg = "YooKassa response missing confirmation URL"
            raise RuntimeError(msg)

        logger.info(
            "YooKassa payment created: id=%s user=%d amount=%d credits=%d",
            payment_id,
            user_id,
            amount_rub,
            credit_amount,
        )

        return PaymentResult(url=confirmation_url, external_id=payment_id)

    async def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """Fetch payment details from YooKassa API by payment ID.

        Used to verify webhook notifications by re-fetching the payment
        directly from YooKassa (more reliable than HMAC signature checks).
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/payments/{payment_id}",
                auth=self._auth,
                timeout=15.0,
            )

        if response.status_code != 200:
            logger.error(
                "YooKassa fetch_payment failed: id=%s status=%d body=%s",
                payment_id,
                response.status_code,
                response.text,
            )
            msg = f"YooKassa API error fetching payment {payment_id}: {response.status_code}"
            raise RuntimeError(msg)

        data: dict[str, Any] = response.json()
        logger.info(
            "YooKassa payment fetched: id=%s status=%s",
            payment_id,
            data.get("status"),
        )
        return data

    async def verify_webhook(
        self, payload: dict[str, Any], signature: str
    ) -> dict[str, Any] | None:
        """Verify a YooKassa webhook notification.

        YooKassa does not use HMAC signatures for webhooks. Instead, we
        extract the payment ID from the notification and re-fetch the
        payment from the API to verify it is genuine and confirm its status.

        Args:
            payload: The webhook JSON body from YooKassa.
            signature: Ignored (YooKassa does not use webhook signatures).

        Returns:
            The fetched payment data dict if verification succeeds, None otherwise.
        """
        payment_object = payload.get("object", {})
        payment_id = payment_object.get("id")

        if not payment_id:
            logger.warning("YooKassa webhook missing payment ID in payload")
            return None

        try:
            return await self.fetch_payment(payment_id)
        except RuntimeError:
            logger.exception("Failed to verify YooKassa webhook for payment %s", payment_id)
            return None
