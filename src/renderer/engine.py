from __future__ import annotations

import io
import logging
import re

from PIL import Image, ImageDraw, ImageFont

from src.config.constants import SLIDE_HEIGHT, SLIDE_WIDTH
from src.renderer.layout import wrap_text
from src.renderer.styles import StyleConfig

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

    def render(
        self,
        heading: str,
        body_text: str,
        background_image: bytes | None = None,
    ) -> bytes:
        """Render a single slide as PNG bytes."""
        s = self.style
        bg_rgb = self._hex_to_rgb(s.bg_color)

        # Create base image
        img: Image.Image
        if background_image:
            try:
                img = Image.open(io.BytesIO(background_image))
                img = img.resize((self.width, self.height), Image.LANCZOS)  # type: ignore[attr-defined]
                img = img.convert("RGBA")

                # Apply dark overlay
                alpha = int(255 * s.overlay_opacity)
                overlay = Image.new("RGBA", (self.width, self.height), (*bg_rgb, alpha))
                img = Image.alpha_composite(img, overlay)
                img = img.convert("RGB")
            except Exception:
                logger.warning("Failed to process background image, using solid color")
                img = Image.new("RGB", (self.width, self.height), bg_rgb)
        else:
            img = Image.new("RGB", (self.width, self.height), bg_rgb)

        draw = ImageDraw.Draw(img)
        padding = s.padding
        max_text_width = self.width - 2 * padding

        # Load fonts (with size reduction for overflow)
        heading_font_size = s.heading_font_size
        body_font_size = s.body_font_size
        heading_font = self._load_font(s.heading_font, heading_font_size)
        body_font = self._load_font(s.body_font, body_font_size)

        text_rgb = self._hex_to_rgb(s.text_color)
        accent_rgb = self._hex_to_rgb(s.accent_color)

        gap = s.heading_body_gap

        # Try reducing font size if text overflows the slide
        max_content_height = self.height - 2 * padding
        for _ in range(5):  # max 5 reduction attempts
            heading_lines = wrap_text(heading, heading_font, max_text_width)
            body_lines = wrap_text(body_text, body_font, max_text_width)

            heading_line_h = heading_font.getbbox("Ag")[3]
            body_line_h = body_font.getbbox("Ag")[3]

            heading_block_h = int(heading_line_h * len(heading_lines) * s.line_spacing)
            body_block_h = int(body_line_h * len(body_lines) * s.line_spacing)
            total_h = heading_block_h + gap + body_block_h

            if total_h <= max_content_height:
                break

            # Reduce both font sizes by ~10%
            heading_font_size = max(24, int(heading_font_size * 0.9))
            body_font_size = max(16, int(body_font_size * 0.9))
            heading_font = self._load_font(s.heading_font, heading_font_size)
            body_font = self._load_font(s.body_font, body_font_size)
        else:
            # Final pass with reduced sizes
            heading_lines = wrap_text(heading, heading_font, max_text_width)
            body_lines = wrap_text(body_text, body_font, max_text_width)
            heading_line_h = heading_font.getbbox("Ag")[3]
            body_line_h = body_font.getbbox("Ag")[3]
            heading_block_h = int(heading_line_h * len(heading_lines) * s.line_spacing)
            body_block_h = int(body_line_h * len(body_lines) * s.line_spacing)
            total_h = heading_block_h + gap + body_block_h

        y_start = (self.height - total_h) // 2

        # Draw heading (accent color)
        y = y_start
        for line in heading_lines:
            if s.heading_alignment == "center":
                bbox = heading_font.getbbox(line)
                line_w = bbox[2] - bbox[0]
                x = (self.width - line_w) // 2
            elif s.heading_alignment == "right":
                bbox = heading_font.getbbox(line)
                line_w = bbox[2] - bbox[0]
                x = self.width - padding - line_w
            else:
                x = padding
            draw.text((x, y), line, font=heading_font, fill=accent_rgb)
            y += int(heading_line_h * s.line_spacing)

        # Draw body
        y += gap
        for line in body_lines:
            draw.text((padding, y), line, font=body_font, fill=text_rgb)
            y += int(body_line_h * s.line_spacing)

        # Export as PNG
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()
