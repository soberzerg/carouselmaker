from __future__ import annotations

import os
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from redis.asyncio import Redis

from src.config.constants import RATE_LIMIT_MESSAGES_PER_MINUTE


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Handle both Message and CallbackQuery
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id
        else:
            return await handler(event, data)

        key = f"throttle:{user_id}"
        now = time.time()
        window = 60  # seconds

        # Check count first before adding
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zcard(key)
        results = await pipe.execute()

        count = results[1]
        if count >= RATE_LIMIT_MESSAGES_PER_MINUTE:
            if isinstance(event, Message):
                await event.answer("Too many requests. Please wait a moment.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Too many requests. Please wait a moment.", show_alert=True)
            return None

        # Only add to sorted set if not throttled (use unique member key)
        unique_member = f"{now}:{os.urandom(4).hex()}"
        pipe2 = self.redis.pipeline()
        pipe2.zadd(key, {unique_member: now})
        pipe2.expire(key, window)
        await pipe2.execute()

        return await handler(event, data)
