from __future__ import annotations

import io
import logging
from pathlib import Path

from PIL import Image

from src.config.constants import SLIDE_HEIGHT, SLIDE_WIDTH
from src.renderer.browser import render_html_to_png
from src.renderer.html_builder import (
    build_comparison_html,
    build_hook_overlay_html,
    build_listing_html,
    build_text_html,
)
from src.renderer.styles import StyleConfig
from src.schemas.slide import (
    ContentTemplate,
    SlideContent,
    SlideType,
    TextPosition,
)

logger = logging.getLogger(__name__)

_CTA_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "cta"


def load_cta_image(style_slug: str) -> bytes | None:
    """Load pre-made CTA image for a style. Returns None if not found."""
    path = _CTA_ASSETS_DIR / f"{style_slug}.png"
    if not path.exists():
        logger.warning("CTA image not found for style '%s' at %s", style_slug, path)
        return None
    return path.read_bytes()


class SlideRenderer:
    def __init__(self, style: StyleConfig) -> None:
        self.style = style
        self.width = SLIDE_WIDTH
        self.height = SLIDE_HEIGHT

    async def render(
        self,
        slide: SlideContent,
        generated_image: bytes | None = None,
        cta_image: bytes | None = None,
    ) -> bytes:
        """Render a single slide as PNG bytes.

        Dispatch logic:
        1. CTA slide + pre-made cta_image -> resize and return (Pillow)
        2. Hook slide + generated_image, no body text -> passthrough
        3. Hook slide + generated_image, with body text -> HTML overlay
        4. Content slide -> HTML template (text/listing/comparison)
        5. Fallback -> HTML text template
        """
        # CTA slide with pre-made image
        if slide.slide_type == SlideType.CTA and cta_image is not None:
            return self._render_cta(cta_image)

        # Hook slide with Gemini image
        if generated_image is not None:
            if slide.text_position == TextPosition.NONE or not slide.body_text:
                return generated_image
            return await self._render_hook_overlay(generated_image, slide)

        # Content slides: dispatch to template renderer
        if slide.slide_type == SlideType.CONTENT:
            return await self._render_content_template(slide)

        # Fallback for any other case
        return await self._render_fallback(slide)

    def _render_cta(self, cta_image_bytes: bytes) -> bytes:
        """Render CTA slide from pre-made image, resizing if needed."""
        img = Image.open(io.BytesIO(cta_image_bytes)).convert("RGB")
        if img.size != (self.width, self.height):
            img = img.resize(
                (self.width, self.height), Image.LANCZOS,  # type: ignore[attr-defined]
            )
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    async def _render_hook_overlay(
        self, image_bytes: bytes, slide: SlideContent,
    ) -> bytes:
        """Overlay body_text on a generated image via HTML template."""
        html = build_hook_overlay_html(slide, self.style, image_bytes)
        return await render_html_to_png(html, self.width, self.height)

    async def _render_content_template(self, slide: SlideContent) -> bytes:
        """Dispatch to the appropriate HTML template."""
        if slide.content_template == ContentTemplate.LISTING and slide.listing_data:
            html = build_listing_html(slide, self.style)
        elif (
            slide.content_template == ContentTemplate.COMPARISON
            and slide.comparison_data
        ):
            html = build_comparison_html(slide, self.style)
        else:
            html = build_text_html(slide, self.style)
        return await render_html_to_png(html, self.width, self.height)

    async def _render_fallback(self, slide: SlideContent) -> bytes:
        """Fallback: render as text template."""
        html = build_text_html(slide, self.style)
        return await render_html_to_png(html, self.width, self.height)
