from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.db.session import AsyncSessionLocal
from src.services.user_service import get_or_create_user


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract user from event
        if (isinstance(event, (Message, CallbackQuery))) and event.from_user:
            tg_user = event.from_user
        else:
            return await handler(event, data)

        async with AsyncSessionLocal() as session:
            db_user = await get_or_create_user(
                session=session,
                telegram_id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name,
            )
            await session.commit()
            data["db_user"] = db_user
            data["db_session"] = session
            return await handler(event, data)
