from __future__ import annotations

import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request

from src.config.settings import get_settings

router = APIRouter(tags=["payments"])
logger = logging.getLogger(__name__)


@router.post("/webhook/yookassa")
async def yookassa_webhook(
    request: Request,
    x_yookassa_signature: str | None = Header(None),
) -> dict[str, str]:
    """YooKassa payment webhook -- stub for MVP."""
    settings = get_settings()
    expected_secret = settings.yookassa.webhook_secret.get_secret_value()

    if not x_yookassa_signature or not hmac.compare_digest(x_yookassa_signature, expected_secret):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    body = await request.json()
    logger.info("YooKassa webhook received: %s", body)

    # TODO: process payment confirmation, credit user account
    return {"status": "ok"}
