from __future__ import annotations

import base64
import logging
from functools import lru_cache
from pathlib import Path

from mako.lookup import TemplateLookup

from src.renderer.styles import StyleConfig
from src.schemas.slide import SlideContent

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = str(Path(__file__).resolve().parent / "templates")
_FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"

_lookup = TemplateLookup(
    directories=[_TEMPLATE_DIR],
    strict_undefined=True,
    input_encoding="utf-8",
    default_filters=["str", "h"],
)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple for rgba() CSS usage."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


@lru_cache(maxsize=1)
def _build_font_faces() -> str:
    """Generate @font-face CSS for .ttf/.otf/.woff2 files in assets/fonts/."""
    if not _FONTS_DIR.exists():
        return ""
    mime_map = {
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".woff2": "font/woff2",
    }
    rules: list[str] = []
    for font_file in sorted(_FONTS_DIR.iterdir()):
        suffix = font_file.suffix.lower()
        if suffix in mime_map:
            mime = mime_map[suffix]
            data = base64.b64encode(font_file.read_bytes()).decode()
            family = font_file.stem.replace("-", " ").replace("_", " ")
            rules.append(
                f"@font-face {{ font-family: '{family}'; "
                f"src: url('data:{mime};base64,{data}'); }}"
            )
    return "\n".join(rules)


def _base_context(style: StyleConfig) -> dict[str, object]:
    """Build the shared template context from StyleConfig."""
    accent_rgb = _hex_to_rgb(style.accent_color)
    bg_rgb = _hex_to_rgb(style.bg_color)
    return {
        "bg_color": style.bg_color,
        "text_color": style.text_color,
        "accent_color": style.accent_color,
        "heading_font_size": style.heading_font_size,
        "body_font_size": style.body_font_size,
        "subtitle_font_size": int(style.heading_font_size * 0.55),
        "heading_font": style.heading_font,
        "body_font": style.body_font,
        "padding": style.padding,
        "line_spacing": style.line_spacing,
        "heading_body_gap": style.heading_body_gap,
        "heading_alignment": style.heading_alignment,
        "font_faces": _build_font_faces(),
        "accent_r": accent_rgb[0],
        "accent_g": accent_rgb[1],
        "accent_b": accent_rgb[2],
        "bg_r": bg_rgb[0],
        "bg_g": bg_rgb[1],
        "bg_b": bg_rgb[2],
    }


def build_text_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render text template HTML."""
    ctx = _base_context(style)
    ctx.update({
        "heading": slide.heading,
        "subtitle": slide.subtitle,
        "body_text": slide.body_text,
        "slide_number": slide.slide_number,
    })
    tmpl = _lookup.get_template("text.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]


def build_listing_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render listing template HTML."""
    assert slide.listing_data is not None
    ctx = _base_context(style)
    ctx.update({
        "heading": slide.heading,
        "subtitle": slide.subtitle,
        "slide_number": slide.slide_number,
        "listing_items": slide.listing_data.items,
    })
    tmpl = _lookup.get_template("listing.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]


def build_comparison_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render comparison template HTML."""
    assert slide.comparison_data is not None
    ctx = _base_context(style)
    ctx.update({
        "slide_number": slide.slide_number,
        "top_label": slide.comparison_data.top_block.label,
        "top_subtitle": slide.comparison_data.top_block.subtitle,
        "top_items": slide.comparison_data.top_block.items,
        "bottom_label": slide.comparison_data.bottom_block.label,
        "bottom_subtitle": slide.comparison_data.bottom_block.subtitle,
        "bottom_items": slide.comparison_data.bottom_block.items,
    })
    tmpl = _lookup.get_template("comparison.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]


def build_quote_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render quote template HTML."""
    assert slide.quote_data is not None
    ctx = _base_context(style)
    ctx.update({
        "slide_number": slide.slide_number,
        "quote_text": slide.quote_data.quote_text,
        "author_name": slide.quote_data.author_name,
        "author_title": slide.quote_data.author_title,
    })
    tmpl = _lookup.get_template("quote.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]


def build_stats_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render stats/big-number template HTML."""
    assert slide.stats_data is not None
    ctx = _base_context(style)
    ctx.update({
        "slide_number": slide.slide_number,
        "heading": slide.heading,
        "stats_value": slide.stats_data.value,
        "stats_label": slide.stats_data.label,
        "stats_context": slide.stats_data.context,
    })
    tmpl = _lookup.get_template("stats.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]


def build_steps_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render steps template HTML."""
    assert slide.steps_data is not None
    ctx = _base_context(style)
    ctx.update({
        "slide_number": slide.slide_number,
        "heading": slide.heading,
        "steps_items": slide.steps_data.items,
    })
    tmpl = _lookup.get_template("steps.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]


def build_hook_overlay_html(
    slide: SlideContent,
    style: StyleConfig,
    image_bytes: bytes,
) -> str:
    """Render hook overlay HTML with generated image as background data URI."""
    b64 = base64.b64encode(image_bytes).decode()
    image_data_uri = f"data:image/png;base64,{b64}"
    ctx = _base_context(style)
    ctx.update({
        "body_text": slide.body_text,
        "text_position": slide.text_position.value,
        "image_data_uri": image_data_uri,
        "body_text_bg_opacity": style.body_text_bg_opacity,
    })
    tmpl = _lookup.get_template("hook_overlay.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]
