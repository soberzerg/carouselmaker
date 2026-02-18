from __future__ import annotations

import io
import logging
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from src.config.constants import OVERLAY_STRIP_PADDING, SLIDE_HEIGHT, SLIDE_WIDTH
from src.renderer.layout import wrap_text
from src.renderer.styles import StyleConfig
from src.schemas.slide import SlideContent, TextPosition

logger = logging.getLogger(__name__)

_HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


class SlideRenderer:
    def __init__(self, style: StyleConfig) -> None:
        self.style = style
        self.width = SLIDE_WIDTH
        self.height = SLIDE_HEIGHT

    def _load_font(self, name: str, size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            logger.warning("Font '%s' not found, using default", name)
            return ImageFont.load_default(size)  # type: ignore[return-value]

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        if not _HEX_COLOR_RE.match(hex_color):
            logger.warning("Invalid hex color '%s', defaulting to black", hex_color)
            return (0, 0, 0)
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    def _align_x(
        self,
        font: ImageFont.FreeTypeFont,
        line: str,
        alignment: str,
        padding: int,
    ) -> int:
        if alignment == "center":
            bbox = font.getbbox(line)
            return int((self.width - (bbox[2] - bbox[0])) // 2)
        if alignment == "right":
            bbox = font.getbbox(line)
            return int(self.width - padding - (bbox[2] - bbox[0]))
        return padding

    def render(
        self,
        slide: SlideContent,
        generated_image: bytes | None = None,
    ) -> bytes:
        """Render a single slide as PNG bytes.

        If generated_image is provided and no body_text overlay is needed,
        the image is returned as-is (passthrough).
        If body_text overlay is needed, it's composited on top.
        If no generated_image, falls back to full Pillow rendering.
        """
        if generated_image is not None:
            if slide.text_position == TextPosition.NONE or not slide.body_text:
                # Passthrough: Gemini image is the final slide
                return generated_image
            # Overlay body_text on top of Gemini image
            return self._overlay_body_text(generated_image, slide)

        # Fallback: full Pillow rendering (no Gemini image)
        return self._fallback_render(slide)

    def _overlay_body_text(self, image_bytes: bytes, slide: SlideContent) -> bytes:
        """Overlay body_text on a generated slide image with semi-transparent strip."""
        s = self.style

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            if img.size != (self.width, self.height):
                img = img.resize((self.width, self.height), Image.LANCZOS)  # type: ignore[attr-defined]
        except Exception:
            logger.warning("Failed to open generated image for overlay, using fallback")
            return self._fallback_render(slide)

        body_font = self._load_font(s.body_font, s.body_font_size)
        text_rgb = self._hex_to_rgb(s.text_color)
        bg_rgb = self._hex_to_rgb(s.bg_color)
        padding = s.padding
        max_text_width = self.width - 2 * padding

        body_lines = wrap_text(slide.body_text, body_font, max_text_width)
        if not body_lines:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="PNG", optimize=True)
            return buf.getvalue()

        body_line_h = body_font.getbbox("Ag")[3]
        body_block_h = int(body_line_h * len(body_lines) * s.line_spacing)
        strip_h = body_block_h + 2 * OVERLAY_STRIP_PADDING

        # Determine strip position
        if slide.text_position == TextPosition.BOTTOM:
            strip_y = self.height - strip_h - padding
        else:
            # Center
            strip_y = (self.height - strip_h) // 2

        # Draw semi-transparent strip
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        alpha = int(255 * s.body_text_bg_opacity)
        draw_overlay.rectangle(
            [(0, strip_y), (self.width, strip_y + strip_h)],
            fill=(*bg_rgb, alpha),
        )
        img = Image.alpha_composite(img, overlay)

        # Draw body text
        draw = ImageDraw.Draw(img)
        y = strip_y + OVERLAY_STRIP_PADDING
        for line in body_lines:
            draw.text((padding, y), line, font=body_font, fill=(*text_rgb, 255))
            y += int(body_line_h * s.line_spacing)

        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def _compute_text_layout(
        self,
        slide: SlideContent,
        heading_font: ImageFont.FreeTypeFont,
        subtitle_font: ImageFont.FreeTypeFont,
        body_font: ImageFont.FreeTypeFont,
        max_text_width: int,
        gap: int,
    ) -> dict[str, Any]:
        """Compute wrapped lines and block heights for all text fields."""
        s = self.style
        h_lines = wrap_text(slide.heading, heading_font, max_text_width)
        st_lines = (
            wrap_text(slide.subtitle, subtitle_font, max_text_width)
            if slide.subtitle else []
        )
        b_lines = (
            wrap_text(slide.body_text, body_font, max_text_width)
            if slide.body_text else []
        )

        h_lh = heading_font.getbbox("Ag")[3]
        st_lh = subtitle_font.getbbox("Ag")[3] if st_lines else 0
        b_lh = body_font.getbbox("Ag")[3] if b_lines else 0

        h_block = int(h_lh * len(h_lines) * s.line_spacing)
        st_block = int(st_lh * len(st_lines) * s.line_spacing) if st_lines else 0
        b_block = int(b_lh * len(b_lines) * s.line_spacing) if b_lines else 0

        st_gap = gap // 2 if st_lines else 0
        b_gap = gap if b_lines else 0
        total = h_block + st_gap + st_block + b_gap + b_block

        return {
            "heading_lines": h_lines,
            "subtitle_lines": st_lines,
            "body_lines": b_lines,
            "heading_line_h": h_lh,
            "subtitle_line_h": st_lh,
            "body_line_h": b_lh,
            "heading_block_h": h_block,
            "subtitle_gap": st_gap,
            "body_gap": b_gap,
            "total_h": total,
        }

    def _fallback_render(self, slide: SlideContent) -> bytes:
        """Full Pillow rendering: heading + subtitle + body on solid color."""
        s = self.style
        bg_rgb = self._hex_to_rgb(s.bg_color)
        img = Image.new("RGB", (self.width, self.height), bg_rgb)
        draw = ImageDraw.Draw(img)

        padding = s.padding
        max_w = self.width - 2 * padding

        h_size = s.heading_font_size
        b_size = s.body_font_size
        st_size = int(s.heading_font_size * 0.55)

        h_font = self._load_font(s.heading_font, h_size)
        b_font = self._load_font(s.body_font, b_size)
        st_font = self._load_font(s.body_font, st_size)

        text_rgb = self._hex_to_rgb(s.text_color)
        accent_rgb = self._hex_to_rgb(s.accent_color)
        gap = s.heading_body_gap
        max_content_h = self.height - 2 * padding

        for _ in range(5):
            layout = self._compute_text_layout(
                slide, h_font, st_font, b_font, max_w, gap,
            )
            if layout["total_h"] <= max_content_h:
                break
            h_size = max(24, int(h_size * 0.9))
            b_size = max(16, int(b_size * 0.9))
            st_size = max(14, int(st_size * 0.9))
            h_font = self._load_font(s.heading_font, h_size)
            b_font = self._load_font(s.body_font, b_size)
            st_font = self._load_font(s.body_font, st_size)
        else:
            layout = self._compute_text_layout(
                slide, h_font, st_font, b_font, max_w, gap,
            )

        y_start = (self.height - layout["total_h"]) // 2

        # Draw heading (accent color)
        y = y_start
        for line in layout["heading_lines"]:
            x = self._align_x(h_font, line, s.heading_alignment, padding)
            draw.text((x, y), line, font=h_font, fill=accent_rgb)
            y += int(layout["heading_line_h"] * s.line_spacing)

        # Draw subtitle
        if layout["subtitle_lines"]:
            y += layout["subtitle_gap"]
            for line in layout["subtitle_lines"]:
                x = self._align_x(st_font, line, s.heading_alignment, padding)
                draw.text((x, y), line, font=st_font, fill=text_rgb)
                y += int(layout["subtitle_line_h"] * s.line_spacing)

        # Draw body
        if layout["body_lines"]:
            y += layout["body_gap"]
            for line in layout["body_lines"]:
                draw.text((padding, y), line, font=b_font, fill=text_rgb)
                y += int(layout["body_line_h"] * s.line_spacing)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()
