from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.credit import CreditTransaction, TransactionType
from src.models.user import User

logger = logging.getLogger(__name__)


async def charge_credits(
    session: AsyncSession,
    user: User,
    amount: int,
) -> bool:
    """Charge credits with SELECT FOR UPDATE to prevent double-spend."""
    stmt = select(User).where(User.id == user.id).with_for_update()
    result = await session.execute(stmt)
    db_user = result.scalar_one()

    if db_user.credit_balance < amount:
        return False

    db_user.credit_balance -= amount

    tx = CreditTransaction(
        user_id=db_user.id,
        amount=-amount,
        transaction_type=TransactionType.GENERATION_CHARGE,
    )
    session.add(tx)
    await session.flush()

    # Update the in-memory user object
    user.credit_balance = db_user.credit_balance
    return True


async def refund_credits(
    session: AsyncSession,
    user_id: int,
    amount: int,
    generation_id: int | None = None,
) -> None:
    """Refund credits on generation failure using SELECT FOR UPDATE."""
    stmt = select(User).where(User.id == user_id).with_for_update()
    result = await session.execute(stmt)
    db_user = result.scalar_one()

    db_user.credit_balance += amount

    tx = CreditTransaction(
        user_id=db_user.id,
        amount=amount,
        transaction_type=TransactionType.REFUND,
        external_payment_id=f"refund_gen_{generation_id}" if generation_id else None,
    )
    session.add(tx)
    await session.flush()
    logger.info("Refunded %d credits to user %d (generation %s)", amount, user_id, generation_id)


async def purchase_credits(
    session: AsyncSession,
    user: User,
    amount: int,
    external_payment_id: str | None = None,
) -> User:
    """Add credits after payment."""
    stmt = select(User).where(User.id == user.id).with_for_update()
    result = await session.execute(stmt)
    db_user = result.scalar_one()

    db_user.credit_balance += amount

    tx = CreditTransaction(
        user_id=db_user.id,
        amount=amount,
        transaction_type=TransactionType.PURCHASE,
        external_payment_id=external_payment_id,
    )
    session.add(tx)
    await session.flush()

    # Update the in-memory user object
    user.credit_balance = db_user.credit_balance
    return db_user
