from __future__ import annotations

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

from src.config.settings import get_settings

router = APIRouter(tags=["webhook"])


@router.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict[str, str]:
    settings = get_settings()
    expected_secret = settings.telegram.webhook_secret.get_secret_value()
    if x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    bot = request.app.state.bot
    dp = request.app.state.dp

    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)

    return {"status": "ok"}
