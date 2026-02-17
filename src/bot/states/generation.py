from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class GenerationFSM(StatesGroup):
    choosing_style = State()
    waiting_text = State()
    generating = State()
