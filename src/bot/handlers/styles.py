from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards.inline import STYLE_DISPLAY_NAMES
from src.config.constants import AVAILABLE_STYLES

router = Router()


@router.message(Command("styles"))
async def cmd_styles(message: Message) -> None:
    lines = ["<b>Available style presets:</b>\n"]
    for slug in AVAILABLE_STYLES:
        name = STYLE_DISPLAY_NAMES.get(slug, slug)
        lines.append(f"  {name}")
    lines.append("\nUse /generate to create a carousel with any style.")
    await message.answer("\n".join(lines))
