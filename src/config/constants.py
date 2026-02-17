from __future__ import annotations

# ── Slide dimensions (Instagram portrait) ────────────────
SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350

# ── Credit system ─────────────────────────────────────────
FREE_CREDITS_ON_START = 3
CREDITS_PER_CAROUSEL = 1

CREDIT_PACKS: list[dict[str, int]] = [
    {"credits": 5, "price_rub": 149},
    {"credits": 15, "price_rub": 349},
    {"credits": 50, "price_rub": 899},
]

# ── Generation limits ─────────────────────────────────────
MAX_SLIDES_PER_CAROUSEL = 10
MIN_SLIDES_PER_CAROUSEL = 3
MAX_INPUT_TEXT_LENGTH = 5000

# ── Rate limiting ─────────────────────────────────────────
RATE_LIMIT_MESSAGES_PER_MINUTE = 10

# ── S3 paths ──────────────────────────────────────────────
S3_CAROUSEL_PREFIX = "carousels"
S3_CLEANUP_DAYS = 30

# ── Style preset slugs ───────────────────────────────────
STYLE_NANO_BANANA = "nano_banana"
STYLE_MINIMALIST = "minimalist"
STYLE_TECH = "tech"
STYLE_CORPORATE = "corporate"

DEFAULT_STYLE = STYLE_NANO_BANANA

AVAILABLE_STYLES = [
    STYLE_NANO_BANANA,
    STYLE_MINIMALIST,
    STYLE_TECH,
    STYLE_CORPORATE,
]
