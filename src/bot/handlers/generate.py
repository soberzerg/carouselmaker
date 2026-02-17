from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.inline import cancel_keyboard, style_picker_keyboard
from src.bot.states.generation import GenerationFSM
from src.config.constants import CREDITS_PER_CAROUSEL, MAX_INPUT_TEXT_LENGTH
from src.models.user import User
from src.services.credit_service import charge_credits
from src.worker.tasks.generate_carousel import generate_carousel_task

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("generate"))
async def cmd_generate(message: Message, state: FSMContext, db_user: User) -> None:
    if db_user.credit_balance < CREDITS_PER_CAROUSEL:
        await message.answer(
            "Not enough credits! Use /buy to purchase more."
        )
        return

    await state.set_state(GenerationFSM.choosing_style)
    await message.answer(
        "Choose a style for your carousel:",
        reply_markup=style_picker_keyboard(),
    )


@router.callback_query(GenerationFSM.choosing_style, F.data.startswith("style:"))
async def on_style_chosen(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not callback.data:
        return
    style_slug = callback.data.split(":", 1)[1]
    await state.update_data(style_slug=style_slug)
    await state.set_state(GenerationFSM.waiting_text)

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Style: <b>{style_slug}</b>\n\n"
        "Now send me the text for your carousel.\n"
        f"(Max {MAX_INPUT_TEXT_LENGTH} characters)",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(GenerationFSM.waiting_text, F.text)
async def on_text_received(
    message: Message,
    state: FSMContext,
    db_user: User,
    db_session: AsyncSession,
) -> None:
    text = message.text or ""
    if len(text) > MAX_INPUT_TEXT_LENGTH:
        await message.answer(
            f"Text is too long ({len(text)} chars). "
            f"Max {MAX_INPUT_TEXT_LENGTH} characters."
        )
        return

    data = await state.get_data()
    style_slug = data.get("style_slug", "nano_banana")

    # Charge credits
    charged = await charge_credits(
        session=db_session,
        user=db_user,
        amount=CREDITS_PER_CAROUSEL,
    )
    if not charged:
        await message.answer("Not enough credits! Use /buy to purchase more.")
        await state.clear()
        return

    await db_session.commit()
    await state.set_state(GenerationFSM.generating)

    status_msg = await message.answer(
        "Generating your carousel... This may take a minute."
    )

    # Dispatch Celery task
    task = generate_carousel_task.delay(
        user_id=db_user.id,
        telegram_chat_id=message.chat.id,
        input_text=text,
        style_slug=style_slug,
        status_message_id=status_msg.message_id,
    )

    logger.info("Carousel task dispatched: %s for user %d", task.id, db_user.id)
    await state.clear()
