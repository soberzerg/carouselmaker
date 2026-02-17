from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards.inline import credit_pack_keyboard
from src.models.user import User

router = Router()


@router.message(Command("credits"))
async def cmd_credits(message: Message, db_user: User) -> None:
    await message.answer(
        f"Your balance: <b>{db_user.credit_balance}</b> credits.\n\nUse /buy to purchase more."
    )


@router.message(Command("buy"))
async def cmd_buy(message: Message) -> None:
    await message.answer(
        "Choose a credit pack:",
        reply_markup=credit_pack_keyboard(),
    )
