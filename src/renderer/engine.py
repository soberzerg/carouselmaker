from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from src.config.constants import (
    COMPARISON_BLOCK_PADDING,
    COMPARISON_BLOCK_RADIUS,
    LISTING_ITEM_GAP,
    OVERLAY_STRIP_PADDING,
    SLIDE_HEIGHT,
    SLIDE_NUMBER_FONT_SIZE,
    SLIDE_WIDTH,
    VS_CIRCLE_RADIUS,
    VS_FONT_SIZE,
)
from src.renderer.layout import wrap_text
from src.renderer.styles import StyleConfig
from src.schemas.slide import (
    ComparisonBlock,
    ContentTemplate,
    SlideContent,
    SlideType,
    TextPosition,
)

logger = logging.getLogger(__name__)

_HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")

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
        cta_image: bytes | None = None,
    ) -> bytes:
        """Render a single slide as PNG bytes.

        Dispatch logic:
        1. CTA slide + pre-made cta_image → resize and return
        2. Hook slide + generated_image → passthrough or overlay body_text
        3. Content slide → template-based Pillow rendering (text/listing/comparison)
        4. Fallback → full Pillow rendering
        """
        # CTA slide with pre-made image
        if slide.slide_type == SlideType.CTA and cta_image is not None:
            return self._render_cta(cta_image)

        # Hook slide with Gemini image
        if generated_image is not None:
            if slide.text_position == TextPosition.NONE or not slide.body_text:
                return generated_image
            return self._overlay_body_text(generated_image, slide)

        # Content slides: dispatch to template renderer
        if slide.slide_type == SlideType.CONTENT:
            return self._render_content_template(slide)

        # Fallback for any other case
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

    # ── CTA rendering ───────────────────────────────────────

    def _render_cta(self, cta_image_bytes: bytes) -> bytes:
        """Render CTA slide from pre-made image, resizing if needed."""
        img = Image.open(io.BytesIO(cta_image_bytes)).convert("RGB")
        if img.size != (self.width, self.height):
            img = img.resize((self.width, self.height), Image.LANCZOS)  # type: ignore[attr-defined]
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    # ── Content template dispatch ───────────────────────────

    def _render_content_template(self, slide: SlideContent) -> bytes:
        """Dispatch to the appropriate template renderer."""
        if slide.content_template == ContentTemplate.LISTING and slide.listing_data:
            return self._render_listing(slide)
        if slide.content_template == ContentTemplate.COMPARISON and slide.comparison_data:
            return self._render_comparison(slide)
        return self._render_text_template(slide)

    # ── Text template ───────────────────────────────────────

    def _render_text_template(self, slide: SlideContent) -> bytes:
        """Text template: heading + optional subtitle + body paragraph + slide number."""
        s = self.style
        bg_rgb = self._hex_to_rgb(s.bg_color)
        img = Image.new("RGB", (self.width, self.height), bg_rgb)
        draw = ImageDraw.Draw(img)

        if slide.slide_number is not None:
            self._draw_slide_number(draw, slide.slide_number)

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

        y = y_start
        for line in layout["heading_lines"]:
            x = self._align_x(h_font, line, s.heading_alignment, padding)
            draw.text((x, y), line, font=h_font, fill=accent_rgb)
            y += int(layout["heading_line_h"] * s.line_spacing)

        if layout["subtitle_lines"]:
            y += layout["subtitle_gap"]
            for line in layout["subtitle_lines"]:
                x = self._align_x(st_font, line, s.heading_alignment, padding)
                draw.text((x, y), line, font=st_font, fill=text_rgb)
                y += int(layout["subtitle_line_h"] * s.line_spacing)

        if layout["body_lines"]:
            y += layout["body_gap"]
            for line in layout["body_lines"]:
                draw.text((padding, y), line, font=b_font, fill=text_rgb)
                y += int(layout["body_line_h"] * s.line_spacing)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()

    # ── Listing template ────────────────────────────────────

    def _render_listing(self, slide: SlideContent) -> bytes:
        """Listing template: heading + subtitle + numbered items."""
        assert slide.listing_data is not None

        s = self.style
        bg_rgb = self._hex_to_rgb(s.bg_color)
        accent_rgb = self._hex_to_rgb(s.accent_color)
        text_rgb = self._hex_to_rgb(s.text_color)
        img = Image.new("RGB", (self.width, self.height), bg_rgb)
        draw = ImageDraw.Draw(img)
        padding = s.padding

        if slide.slide_number is not None:
            self._draw_slide_number(draw, slide.slide_number)

        h_size = s.heading_font_size
        st_size = int(s.heading_font_size * 0.55)
        item_size = s.body_font_size
        max_w = self.width - 2 * padding

        h_font = self._load_font(s.heading_font, h_size)
        st_font = self._load_font(s.body_font, st_size)
        item_font = self._load_font(s.body_font, item_size)
        num_font = self._load_font(s.heading_font, item_size)

        # Reserve top space for slide number
        y_top = padding + (60 if slide.slide_number is not None else 0)

        # Compute number prefix width (widest possible: "8. ")
        num_prefix_w = int(num_font.getbbox("8. ")[2]) + 10

        items = slide.listing_data.items

        # Font-shrink loop
        for _ in range(5):
            total_h = self._compute_listing_height(
                slide, h_font, st_font, item_font, num_font,
                max_w, num_prefix_w, items, s,
            )
            if total_h <= self.height - y_top - padding:
                break
            h_size = max(24, int(h_size * 0.9))
            item_size = max(16, int(item_size * 0.9))
            st_size = max(14, int(st_size * 0.9))
            h_font = self._load_font(s.heading_font, h_size)
            st_font = self._load_font(s.body_font, st_size)
            item_font = self._load_font(s.body_font, item_size)
            num_font = self._load_font(s.heading_font, item_size)
            num_prefix_w = int(num_font.getbbox("8. ")[2]) + 10

        # Draw heading
        y = y_top
        h_lines = wrap_text(slide.heading, h_font, max_w)
        h_lh = h_font.getbbox("Ag")[3]
        for line in h_lines:
            x = self._align_x(h_font, line, s.heading_alignment, padding)
            draw.text((x, y), line, font=h_font, fill=accent_rgb)
            y += int(h_lh * s.line_spacing)

        # Draw subtitle
        if slide.subtitle:
            y += s.heading_body_gap // 2
            st_lines = wrap_text(slide.subtitle, st_font, max_w)
            st_lh = st_font.getbbox("Ag")[3]
            for line in st_lines:
                x = self._align_x(st_font, line, s.heading_alignment, padding)
                draw.text((x, y), line, font=st_font, fill=text_rgb)
                y += int(st_lh * s.line_spacing)

        # Draw numbered list
        y += s.heading_body_gap
        item_lh = item_font.getbbox("Ag")[3]
        item_max_w = max_w - num_prefix_w

        for i, item in enumerate(items, start=1):
            num_str = f"{i}."
            draw.text((padding, y), num_str, font=num_font, fill=accent_rgb)

            item_lines = wrap_text(item, item_font, item_max_w)
            for line in item_lines:
                draw.text((padding + num_prefix_w, y), line, font=item_font, fill=text_rgb)
                y += int(item_lh * s.line_spacing)
            y += LISTING_ITEM_GAP

        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()

    def _compute_listing_height(
        self,
        slide: SlideContent,
        h_font: ImageFont.FreeTypeFont,
        st_font: ImageFont.FreeTypeFont,
        item_font: ImageFont.FreeTypeFont,
        num_font: ImageFont.FreeTypeFont,
        max_w: int,
        num_prefix_w: int,
        items: list[str],
        s: StyleConfig,
    ) -> int:
        """Compute total height of listing layout for font-shrink loop."""
        h_lines = wrap_text(slide.heading, h_font, max_w)
        h_lh = h_font.getbbox("Ag")[3]
        total = int(h_lh * len(h_lines) * s.line_spacing)

        if slide.subtitle:
            total += s.heading_body_gap // 2
            st_lines = wrap_text(slide.subtitle, st_font, max_w)
            st_lh = st_font.getbbox("Ag")[3]
            total += int(st_lh * len(st_lines) * s.line_spacing)

        total += s.heading_body_gap
        item_lh = item_font.getbbox("Ag")[3]
        item_max_w = max_w - num_prefix_w

        for item in items:
            item_lines = wrap_text(item, item_font, item_max_w)
            total += int(item_lh * len(item_lines) * s.line_spacing) + LISTING_ITEM_GAP

        return total

    # ── Comparison (VS) template ────────────────────────────

    def _render_comparison(self, slide: SlideContent) -> bytes:
        """Comparison template: heading + top block + VS + bottom block."""
        assert slide.comparison_data is not None

        s = self.style
        bg_rgb = self._hex_to_rgb(s.bg_color)
        accent_rgb = self._hex_to_rgb(s.accent_color)
        text_rgb = self._hex_to_rgb(s.text_color)
        img = Image.new("RGBA", (self.width, self.height), (*bg_rgb, 255))
        draw = ImageDraw.Draw(img)
        padding = s.padding
        max_w = self.width - 2 * padding

        if slide.slide_number is not None:
            self._draw_slide_number(draw, slide.slide_number)

        comp = slide.comparison_data

        # Reserve top space for slide number
        y_top = padding + (60 if slide.slide_number is not None else 0)

        h_size = s.heading_font_size
        st_size = int(s.heading_font_size * 0.55)

        h_font = self._load_font(s.heading_font, h_size)
        st_font = self._load_font(s.body_font, st_size)

        # Draw heading
        y = y_top
        h_lines = wrap_text(slide.heading, h_font, max_w)
        h_lh = h_font.getbbox("Ag")[3]
        for line in h_lines:
            x = self._align_x(h_font, line, s.heading_alignment, padding)
            draw.text((x, y), line, font=h_font, fill=accent_rgb)
            y += int(h_lh * s.line_spacing)

        # Draw subtitle
        if slide.subtitle:
            y += s.heading_body_gap // 2
            st_lines = wrap_text(slide.subtitle, st_font, max_w)
            st_lh = st_font.getbbox("Ag")[3]
            for line in st_lines:
                x = self._align_x(st_font, line, s.heading_alignment, padding)
                draw.text((x, y), line, font=st_font, fill=text_rgb)
                y += int(st_lh * s.line_spacing)

        y += s.heading_body_gap

        # Calculate block zones
        vs_zone_h = VS_CIRCLE_RADIUS * 2 + 20
        available_h = self.height - y - padding
        block_h = (available_h - vs_zone_h) // 2

        # Draw top block
        self._draw_comparison_block(draw, comp.top_block, padding, y, max_w, block_h, s)
        y += block_h

        # Draw VS separator
        vs_center_y = y + vs_zone_h // 2
        self._draw_vs_separator(draw, vs_center_y)
        y += vs_zone_h

        # Draw bottom block
        self._draw_comparison_block(draw, comp.bottom_block, padding, y, max_w, block_h, s)

        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    # ── Drawing helpers ─────────────────────────────────────

    def _draw_slide_number(self, draw: ImageDraw.ImageDraw, number: int) -> None:
        """Draw slide number badge in top-right corner."""
        s = self.style
        accent_rgb = self._hex_to_rgb(s.accent_color)
        bg_rgb = self._hex_to_rgb(s.bg_color)
        font = self._load_font(s.heading_font, SLIDE_NUMBER_FONT_SIZE)
        text = f"{number:02d}"

        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        circle_r = max(tw, th) // 2 + 12
        cx = self.width - s.padding - circle_r
        cy = s.padding + circle_r

        draw.ellipse(
            [(cx - circle_r, cy - circle_r), (cx + circle_r, cy + circle_r)],
            fill=accent_rgb,
        )
        draw.text(
            (cx - tw // 2, cy - th // 2),
            text, font=font, fill=bg_rgb,
        )

    def _draw_vs_separator(self, draw: ImageDraw.ImageDraw, center_y: int) -> None:
        """Draw horizontal line with 'VS' circle in the middle."""
        s = self.style
        accent_rgb = self._hex_to_rgb(s.accent_color)
        bg_rgb = self._hex_to_rgb(s.bg_color)
        padding = s.padding

        draw.line(
            [(padding, center_y), (self.width - padding, center_y)],
            fill=accent_rgb, width=2,
        )

        vs_font = self._load_font(s.heading_font, VS_FONT_SIZE)
        r = VS_CIRCLE_RADIUS
        cx = self.width // 2
        draw.ellipse(
            [(cx - r, center_y - r), (cx + r, center_y + r)],
            fill=accent_rgb,
        )
        bbox = vs_font.getbbox("VS")
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (cx - tw // 2, center_y - th // 2),
            "VS", font=vs_font, fill=bg_rgb,
        )

    def _draw_comparison_block(
        self,
        draw: ImageDraw.ImageDraw,
        block: ComparisonBlock,
        x: int,
        y: int,
        width: int,
        height: int,
        s: StyleConfig,
    ) -> None:
        """Draw a comparison block (label + items) within a rounded rect."""
        accent_rgb = self._hex_to_rgb(s.accent_color)
        text_rgb = self._hex_to_rgb(s.text_color)

        block_bg = (*accent_rgb, 30)
        draw.rounded_rectangle(
            [(x, y), (x + width, y + height)],
            radius=COMPARISON_BLOCK_RADIUS,
            fill=block_bg,
            outline=accent_rgb,
            width=2,
        )

        inner_pad = COMPARISON_BLOCK_PADDING
        label_font = self._load_font(s.heading_font, int(s.body_font_size * 1.2))
        item_font = self._load_font(s.body_font, s.body_font_size)
        inner_max_w = width - 2 * inner_pad

        cy = y + inner_pad
        label_lines = wrap_text(block.label, label_font, inner_max_w)
        label_lh = label_font.getbbox("Ag")[3]
        for line in label_lines:
            draw.text((x + inner_pad, cy), line, font=label_font, fill=accent_rgb)
            cy += int(label_lh * 1.3)

        cy += 8
        item_lh = item_font.getbbox("Ag")[3]
        for item in block.items:
            bullet = f"\u2022 {item}"
            item_lines = wrap_text(bullet, item_font, inner_max_w)
            for line in item_lines:
                draw.text((x + inner_pad, cy), line, font=item_font, fill=text_rgb)
                cy += int(item_lh * s.line_spacing)
