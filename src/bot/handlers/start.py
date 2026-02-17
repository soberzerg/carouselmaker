from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards.reply import main_menu_keyboard
from src.models.user import User

router = Router()

WELCOME_TEXT = (
    "Welcome to <b>Nano Banana Carousel Maker</b>!\n\n"
    "I create viral carousels for LinkedIn and Instagram.\n"
    "Just send me text and pick a style — I'll generate professional slides in minutes.\n\n"
    "You have <b>{credits}</b> free credits to get started.\n\n"
    "Use /generate to create your first carousel!"
)

HELP_TEXT = (
    "<b>Available commands:</b>\n\n"
    "/generate — Create a new carousel\n"
    "/styles — Browse style presets\n"
    "/credits — Check your credit balance\n"
    "/buy — Purchase more credits\n"
    "/help — Show this message"
)


@router.message(Command("start"))
async def cmd_start(message: Message, db_user: User) -> None:
    await message.answer(
        WELCOME_TEXT.format(credits=db_user.credit_balance),
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)
