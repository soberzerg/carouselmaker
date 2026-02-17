from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/generate"), KeyboardButton(text="/styles")],
            [KeyboardButton(text="/credits"), KeyboardButton(text="/help")],
        ],
        resize_keyboard=True,
    )
