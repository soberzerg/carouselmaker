from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.constants import CREDIT_PACKS
from src.models.user import User
from src.services.credit_service import purchase_credits

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "cancel")
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Cancelled.")  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def on_buy_pack(
    callback: CallbackQuery,
    db_user: User,
    db_session: AsyncSession,
) -> None:
    if not callback.data:
        return

    pack_index = int(callback.data.split(":", 1)[1])
    if pack_index < 0 or pack_index >= len(CREDIT_PACKS):
        await callback.answer("Invalid pack", show_alert=True)
        return

    pack = CREDIT_PACKS[pack_index]

    # Stub: immediately credit user (no real payment flow)
    await purchase_credits(
        session=db_session,
        user=db_user,
        amount=pack["credits"],
        external_payment_id=f"stub_{db_user.telegram_id}_{pack_index}",
    )
    await db_session.commit()

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Added <b>{pack['credits']}</b> credits!\n"
        f"New balance: <b>{db_user.credit_balance}</b>"
    )
    await callback.answer("Credits added!")
