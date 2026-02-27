from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.config.settings import get_settings
from src.models.payment import Payment, PaymentStatus
from src.models.user import User
from src.payments.yookassa_provider import YooKassaProvider
from src.services.credit_service import purchase_credits

router = APIRouter(tags=["payments"])
logger = logging.getLogger(__name__)


def _get_provider() -> YooKassaProvider:
    """Build a YooKassaProvider from current settings."""
    settings = get_settings()
    return YooKassaProvider(
        shop_id=settings.yookassa.shop_id,
        secret_key=settings.yookassa.secret_key.get_secret_value(),
        return_url=settings.yookassa.return_url,
    )


async def _notify_user_telegram(telegram_id: int, text: str) -> None:
    """Send a Telegram message to a user via the Bot HTTP API (httpx).

    This is used from the webhook handler to notify users about payment outcomes
    without depending on the aiogram Bot instance.
    """
    settings = get_settings()
    token = settings.telegram.bot_token.get_secret_value()
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "chat_id": telegram_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=10.0,
            )
        if response.status_code != 200:
            logger.warning(
                "Telegram notification failed: status=%d body=%s",
                response.status_code,
                response.text,
            )
    except Exception:
        logger.exception("Failed to send Telegram notification to user %d", telegram_id)


@router.post("/webhook/yookassa")
async def yookassa_webhook(
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),  # noqa: B008
) -> dict[str, str]:
    """Handle YooKassa payment notifications.

    YooKassa sends POST requests with JSON body containing:
    {
        "type": "notification",
        "event": "payment.succeeded" | "payment.canceled" | ...,
        "object": { ... payment object ... }
    }

    Verification: We re-fetch the payment from YooKassa API using the payment ID
    rather than relying on HMAC signatures (YooKassa recommendation).
    """
    body: dict[str, Any] = await request.json()
    event = body.get("event", "")
    payment_object = body.get("object", {})
    yookassa_payment_id: str | None = payment_object.get("id")

    logger.info(
        "YooKassa webhook received: event=%s payment_id=%s",
        event,
        yookassa_payment_id,
    )

    if not yookassa_payment_id:
        raise HTTPException(status_code=400, detail="Missing payment ID in notification")

    # Verify the notification by re-fetching the payment from YooKassa API
    provider = _get_provider()
    try:
        real_payment = await provider.fetch_payment(yookassa_payment_id)
    except RuntimeError as exc:
        logger.exception("Failed to fetch payment %s from YooKassa", yookassa_payment_id)
        raise HTTPException(
            status_code=502, detail="Failed to verify payment with YooKassa"
        ) from exc

    real_status = real_payment.get("status", "")

    # Look up our Payment record
    stmt = select(Payment).where(Payment.yookassa_payment_id == yookassa_payment_id)
    result = await db_session.execute(stmt)
    db_payment = result.scalar_one_or_none()

    if db_payment is None:
        logger.warning(
            "YooKassa webhook for unknown payment: %s (event=%s)",
            yookassa_payment_id,
            event,
        )
        # Return 200 to prevent YooKassa from retrying
        return {"status": "ok"}

    if event == "payment.succeeded" and real_status == "succeeded":
        if db_payment.status == PaymentStatus.PENDING:
            # Credit the user
            user_stmt = select(User).where(User.id == db_payment.user_id)
            user_result = await db_session.execute(user_stmt)
            db_user = user_result.scalar_one_or_none()

            if db_user is None:
                logger.error(
                    "Payment %s references non-existent user_id=%d",
                    yookassa_payment_id,
                    db_payment.user_id,
                )
                return {"status": "ok"}

            db_payment.status = PaymentStatus.SUCCEEDED
            await purchase_credits(
                session=db_session,
                user=db_user,
                amount=db_payment.credit_amount,
                external_payment_id=yookassa_payment_id,
            )
            await db_session.commit()

            logger.info(
                "Payment succeeded: id=%s user=%d credits=%d",
                yookassa_payment_id,
                db_payment.user_id,
                db_payment.credit_amount,
            )

            # Notify user via Telegram
            await _notify_user_telegram(
                telegram_id=db_user.telegram_id,
                text=(
                    f"Payment successful! <b>{db_payment.credit_amount}</b> credits added.\n"
                    f"New balance: <b>{db_user.credit_balance}</b> credits."
                ),
            )
        else:
            logger.info(
                "Payment %s already processed (status=%s), skipping",
                yookassa_payment_id,
                db_payment.status,
            )

    elif event == "payment.canceled" and real_status == "canceled":
        if db_payment.status == PaymentStatus.PENDING:
            db_payment.status = PaymentStatus.CANCELED
            await db_session.commit()

            logger.info("Payment canceled: id=%s user=%d", yookassa_payment_id, db_payment.user_id)

            # Notify user about cancellation
            user_stmt = select(User).where(User.id == db_payment.user_id)
            user_result = await db_session.execute(user_stmt)
            db_user = user_result.scalar_one_or_none()
            if db_user:
                await _notify_user_telegram(
                    telegram_id=db_user.telegram_id,
                    text="Your payment was canceled. No credits were charged.",
                )
        else:
            logger.info(
                "Payment %s already processed (status=%s), skipping cancellation",
                yookassa_payment_id,
                db_payment.status,
            )

    else:
        logger.info(
            "YooKassa webhook event=%s real_status=%s — no action taken",
            event,
            real_status,
        )

    return {"status": "ok"}
