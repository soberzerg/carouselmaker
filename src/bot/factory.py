from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.handlers import callbacks, generate, start, styles
from src.bot.handlers import credits as credits_handler
from src.bot.middlewares.auth import AuthMiddleware
from src.bot.middlewares.throttle import ThrottleMiddleware
from src.config.settings import Settings


def create_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.telegram.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(settings: Settings) -> Dispatcher:
    storage = RedisStorage.from_url(settings.redis.url)
    dp = Dispatcher(storage=storage)

    # Register middlewares
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(ThrottleMiddleware(settings.redis.url))

    # Register handlers
    dp.include_router(start.router)
    dp.include_router(generate.router)
    dp.include_router(credits_handler.router)
    dp.include_router(styles.router)
    dp.include_router(callbacks.router)

    return dp
