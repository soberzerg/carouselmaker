from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from redis.asyncio import Redis

from src.config.constants import RATE_LIMIT_MESSAGES_PER_MINUTE


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self, redis_url: str) -> None:
        self.redis = Redis.from_url(redis_url)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        key = f"throttle:{user_id}"
        now = time.time()
        window = 60  # seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()

        count = results[2]
        if count > RATE_LIMIT_MESSAGES_PER_MINUTE:
            await event.answer("Too many requests. Please wait a moment.")
            return None

        return await handler(event, data)
