from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routers import admin, health, payments, webhook
from src.bot.factory import create_bot, create_dispatcher
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()

    # Create bot & dispatcher
    bot = create_bot(settings)
    dp = create_dispatcher(settings)

    # Store on app state for webhook access
    app.state.bot = bot
    app.state.dp = dp

    # Set webhook
    webhook_url = settings.telegram.webhook_url
    if webhook_url:
        webhook_secret = settings.telegram.webhook_secret.get_secret_value()
        await bot.set_webhook(
            url=webhook_url,
            secret_token=webhook_secret,
            drop_pending_updates=True,
        )
        logger.info("Telegram webhook set: %s", webhook_url)

    yield

    # Cleanup
    if webhook_url:
        await bot.delete_webhook()
    await bot.session.close()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Nano Banana Carousel Maker",
        version="0.1.0",
        debug=settings.is_dev,
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(webhook.router)
    app.include_router(admin.router)
    app.include_router(payments.router)

    return app
