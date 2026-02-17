from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constants import FREE_CREDITS_ON_START
from src.models.credit import CreditTransaction, TransactionType
from src.models.user import User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        # Update profile fields if changed
        if username and user.username != username:
            user.username = username
        if full_name and user.full_name != full_name:
            user.full_name = full_name
        return user

    # Create new user with welcome bonus
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        credit_balance=FREE_CREDITS_ON_START,
    )
    session.add(user)
    await session.flush()

    # Record welcome bonus transaction
    tx = CreditTransaction(
        user_id=user.id,
        amount=FREE_CREDITS_ON_START,
        transaction_type=TransactionType.WELCOME_BONUS,
    )
    session.add(tx)
    await session.flush()

    return user
