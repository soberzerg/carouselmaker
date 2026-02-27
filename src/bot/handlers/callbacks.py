from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.states.generation import GenerationFSM
from src.config.constants import CREDIT_PACKS
from src.config.settings import get_settings
from src.models.payment import Payment, PaymentStatus
from src.models.user import User
from src.payments.yookassa_provider import YooKassaProvider

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == "cancel",
    StateFilter(GenerationFSM.choosing_style, GenerationFSM.waiting_text),
)
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
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

    raw_index = callback.data.split(":", 1)[1]
    try:
        pack_index = int(raw_index)
    except ValueError:
        await callback.answer("Invalid pack", show_alert=True)
        return

    if pack_index < 0 or pack_index >= len(CREDIT_PACKS):
        await callback.answer("Invalid pack", show_alert=True)
        return

    pack = CREDIT_PACKS[pack_index]

    # Create a real YooKassa payment
    settings = get_settings()
    provider = YooKassaProvider(
        shop_id=settings.yookassa.shop_id,
        secret_key=settings.yookassa.secret_key.get_secret_value(),
        return_url=settings.yookassa.return_url,
    )

    try:
        payment_result = await provider.create_payment(
            user_id=db_user.id,
            amount_rub=pack.price_rub,
            credit_amount=pack.credits,
        )
    except RuntimeError:
        logger.exception("Failed to create YooKassa payment for user %d", db_user.id)
        await callback.answer("Payment service unavailable. Try again later.", show_alert=True)
        return

    # Save Payment record in DB with PENDING status
    db_payment = Payment(
        user_id=db_user.id,
        yookassa_payment_id=payment_result.external_id,
        amount_rub=pack.price_rub,
        credit_amount=pack.credits,
        status=PaymentStatus.PENDING,
    )
    db_session.add(db_payment)
    await db_session.commit()

    logger.info(
        "Payment created: yookassa_id=%s user=%d amount=%d credits=%d",
        payment_result.external_id,
        db_user.id,
        pack.price_rub,
        pack.credits,
    )

    # Send payment link to user
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Pay {pack.price_rub} RUB", url=payment_result.url)],
        ]
    )

    if callback.message:
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"<b>{pack.credits} credits</b> for <b>{pack.price_rub} RUB</b>\n\n"
            "Click the button below to pay. Credits will be added automatically "
            "after the payment is confirmed.",
            reply_markup=keyboard,
        )
    await callback.answer()
