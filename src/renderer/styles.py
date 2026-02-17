from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, fields
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "templates"

STYLE_DESCRIPTIONS: dict[str, str] = {
    "nano_banana": (
        "Bold, high-contrast yellow (#FFD600) and black (#1A1A1A), energetic and attention-grabbing"
    ),
    "minimalist": "Clean white and light grey, modern sans-serif, elegant spacing",
    "tech": "Dark blue (#0A1628) with cyan (#00E5FF) accents, futuristic vibe",
    "corporate": "Navy blue (#1B2A4A) with white text, professional and trustworthy",
}


@dataclass
class StyleConfig:
    slug: str
    name: str
    bg_color: str = "#1A1A1A"
    text_color: str = "#FFFFFF"
    accent_color: str = "#FFD600"
    heading_font_size: int = 72
    body_font_size: int = 36
    heading_font: str = "Arial"
    body_font: str = "Arial"
    overlay_opacity: float = 0.6
    padding: int = 80
    line_spacing: float = 1.4
    heading_body_gap: int = 40
    heading_alignment: str = "left"
    extra: dict[str, object] = field(default_factory=dict)


# Field names that map directly from JSON to StyleConfig
_STYLE_FIELD_NAMES = {f.name for f in fields(StyleConfig) if f.name not in ("slug", "extra")}


@lru_cache(maxsize=16)
def load_style_config(slug: str) -> StyleConfig:
    """Load style config from JSON template file."""
    if not ASSETS_DIR.exists():
        logger.warning("Assets directory not found: %s, using defaults", ASSETS_DIR)
        return StyleConfig(slug=slug, name=slug.replace("_", " ").title())

    path = ASSETS_DIR / f"{slug}.json"
    if not path.exists():
        return StyleConfig(slug=slug, name=slug.replace("_", " ").title())

    with open(path) as f:
        data = json.load(f)

    kwargs: dict[str, object] = {"slug": slug}
    for field_name in _STYLE_FIELD_NAMES:
        if field_name in data:
            kwargs[field_name] = data[field_name]
        elif field_name == "name":
            kwargs["name"] = data.get("name", slug)
    kwargs["extra"] = data.get("extra", {})

    return StyleConfig(**kwargs)  # type: ignore[arg-type]
