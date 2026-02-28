from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram.types import BotCommand
from fastapi import FastAPI

from src.api.routers import admin, health, payments, webhook
from src.bot.factory import create_bot, create_dispatcher
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    # Create bot & dispatcher
    bot = create_bot(settings)
    dp = create_dispatcher(settings)

    # Store on app state for webhook access
    app.state.bot = bot
    app.state.dp = dp

    # Set bot commands menu
    await bot.set_my_commands(
        [
            BotCommand(command="generate", description="Создать карусель"),
            BotCommand(command="styles", description="Стили оформления"),
            BotCommand(command="credits", description="Мой баланс"),
            BotCommand(command="buy", description="Купить кредиты"),
            BotCommand(command="help", description="Помощь"),
        ]
    )

    # Set bot profile texts
    await bot.set_my_name(name="Карусель-мейкер")
    await bot.set_my_short_description(
        short_description="🍌 Делаю карусели для LinkedIn и Instagram. Просто скинь текст — остальное на мне."
    )
    await bot.set_my_description(
        description=(
            "🍌 Текст → виральная карусель за минуту.\n"
            "\n"
            "Что умеет:\n"
            "• AI-копирайтинг для слайдов\n"
            "• 10 стилей оформления\n"
            "• AI-генерация изображений\n"
            "• Готовые PNG 1080×1350\n"
            "\n"
            "3 бесплатных карусели при старте.\n"
            "Жми «Запустить» 🚀"
        )
    )
    logger.info("Bot profile configured")

    # Set webhook or start polling
    webhook_url = settings.telegram.webhook_url
    polling_task: asyncio.Task[None] | None = None

    if webhook_url:
        webhook_secret = settings.telegram.webhook_secret.get_secret_value()
        await bot.set_webhook(
            url=webhook_url,
            secret_token=webhook_secret,
            drop_pending_updates=True,
        )
        logger.info("Telegram webhook set: %s", webhook_url)
    else:
        logger.info("No webhook URL configured — starting long-polling mode")
        polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))

    yield

    # Cleanup
    if polling_task is not None:
        polling_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await polling_task
    if webhook_url:
        await bot.delete_webhook()
    await bot.session.close()

    # Close middleware Redis connection
    middleware_redis = dp.get("middleware_redis")
    if middleware_redis is not None:
        await middleware_redis.aclose()


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
