from __future__ import annotations

from src.config.constants import AVAILABLE_STYLES
from src.renderer.styles import StyleConfig, load_style_config


def list_presets() -> list[StyleConfig]:
    return [load_style_config(slug) for slug in AVAILABLE_STYLES]


def get_preset_config(slug: str) -> StyleConfig:
    return load_style_config(slug)
