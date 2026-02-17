from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

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
    extra: dict[str, object] = field(default_factory=dict)


def load_style_config(slug: str) -> StyleConfig:
    """Load style config from JSON template file."""
    path = ASSETS_DIR / f"{slug}.json"
    if not path.exists():
        return StyleConfig(slug=slug, name=slug.replace("_", " ").title())

    with open(path) as f:
        data = json.load(f)

    return StyleConfig(
        slug=slug,
        name=data.get("name", slug),
        bg_color=data.get("bg_color", "#1A1A1A"),
        text_color=data.get("text_color", "#FFFFFF"),
        accent_color=data.get("accent_color", "#FFD600"),
        heading_font_size=data.get("heading_font_size", 72),
        body_font_size=data.get("body_font_size", 36),
        heading_font=data.get("heading_font", "Arial"),
        body_font=data.get("body_font", "Arial"),
        overlay_opacity=data.get("overlay_opacity", 0.6),
        padding=data.get("padding", 80),
        line_spacing=data.get("line_spacing", 1.4),
        extra=data.get("extra", {}),
    )
