from __future__ import annotations

import io
import logging

from PIL import Image, ImageDraw, ImageFont

from src.config.constants import SLIDE_HEIGHT, SLIDE_WIDTH
from src.renderer.layout import wrap_text
from src.renderer.styles import StyleConfig

logger = logging.getLogger(__name__)


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
            return ImageFont.load_default(size)  # type: ignore[call-arg]

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
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
        if background_image:
            try:
                img = Image.open(io.BytesIO(background_image))
                img = img.resize((self.width, self.height), Image.LANCZOS)
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

        # Load fonts
        heading_font = self._load_font(s.heading_font, s.heading_font_size)
        body_font = self._load_font(s.body_font, s.body_font_size)

        text_rgb = self._hex_to_rgb(s.text_color)
        accent_rgb = self._hex_to_rgb(s.accent_color)

        # Wrap text
        heading_lines = wrap_text(heading, heading_font, max_text_width)
        body_lines = wrap_text(body_text, body_font, max_text_width)

        # Calculate vertical positioning (centered)
        heading_line_h = heading_font.getbbox("Ag")[3]
        body_line_h = body_font.getbbox("Ag")[3]

        heading_block_h = int(heading_line_h * len(heading_lines) * s.line_spacing)
        body_block_h = int(body_line_h * len(body_lines) * s.line_spacing)
        gap = 40  # gap between heading and body
        total_h = heading_block_h + gap + body_block_h

        y_start = (self.height - total_h) // 2

        # Draw heading (accent color)
        y = y_start
        for line in heading_lines:
            draw.text((padding, y), line, font=heading_font, fill=accent_rgb)
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
