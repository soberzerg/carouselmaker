from __future__ import annotations

from dataclasses import dataclass

# ── Slide dimensions (Instagram portrait) ────────────────
SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350

# ── Credit system ─────────────────────────────────────────
FREE_CREDITS_ON_START = 3
CREDITS_PER_CAROUSEL = 1


@dataclass(frozen=True, slots=True)
class CreditPack:
    credits: int
    price_rub: int


CREDIT_PACKS: tuple[CreditPack, ...] = (
    CreditPack(credits=5, price_rub=149),
    CreditPack(credits=15, price_rub=349),
    CreditPack(credits=50, price_rub=899),
)

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

AVAILABLE_STYLES: tuple[str, ...] = (
    STYLE_NANO_BANANA,
    STYLE_MINIMALIST,
    STYLE_TECH,
    STYLE_CORPORATE,
)

# ── Image generation ─────────────────────────────────────
IMAGE_GEN_MAX_RETRIES = 2
IMAGE_GEN_RETRY_BACKOFF = 1.0

# ── Rendering ────────────────────────────────────────────
OVERLAY_STRIP_PADDING = 30

# ── Style display names ──────────────────────────────────
STYLE_DISPLAY_NAMES: dict[str, str] = {
    STYLE_NANO_BANANA: "Nano Banana",
    STYLE_MINIMALIST: "Minimalist",
    STYLE_TECH: "Tech",
    STYLE_CORPORATE: "Corporate",
}
