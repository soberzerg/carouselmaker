from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.config.constants import AVAILABLE_STYLES, CREDIT_PACKS, STYLE_DISPLAY_NAMES


def style_picker_keyboard() -> InlineKeyboardMarkup:
    all_buttons = [
        InlineKeyboardButton(
            text=STYLE_DISPLAY_NAMES.get(slug, slug),
            callback_data=f"style:{slug}",
        )
        for slug in AVAILABLE_STYLES
    ]
    rows = [all_buttons[i : i + 2] for i in range(0, len(all_buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def credit_pack_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{pack.credits} credits \u2014 {pack.price_rub} RUB",
                callback_data=f"buy:{i}",
            )
        ]
        for i, pack in enumerate(CREDIT_PACKS)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Cancel", callback_data="cancel")]]
    )
