from __future__ import annotations

import io

from PIL import Image

from src.config.constants import SLIDE_HEIGHT, SLIDE_WIDTH
from src.renderer.engine import SlideRenderer
from src.renderer.styles import StyleConfig
from src.schemas.slide import SlideContent, SlideType, TextPosition


def _make_style() -> StyleConfig:
    return StyleConfig(slug="test", name="Test Style")


def _make_png(width: int = SLIDE_WIDTH, height: int = SLIDE_HEIGHT) -> bytes:
    """Create a valid PNG image in memory."""
    img = Image.new("RGB", (width, height), (100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _png_dimensions(data: bytes) -> tuple[int, int]:
    img = Image.open(io.BytesIO(data))
    return img.size


class TestPassthrough:
    def test_returns_image_as_is_when_no_body_text(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=0,
            heading="Hook Slide",
            subtitle="Subtitle here",
            body_text="",
            text_position=TextPosition.NONE,
            slide_type=SlideType.HOOK,
        )
        gen_image = _make_png()
        result = renderer.render(slide=slide, generated_image=gen_image)
        assert result == gen_image

    def test_returns_image_as_is_when_text_position_none(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=1,
            heading="Content",
            subtitle="",
            body_text="Some text",
            text_position=TextPosition.NONE,
            slide_type=SlideType.CONTENT,
        )
        gen_image = _make_png()
        result = renderer.render(slide=slide, generated_image=gen_image)
        # text_position=none means passthrough even if body_text exists
        assert result == gen_image


class TestOverlay:
    def test_overlay_produces_valid_png(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=1,
            heading="Content Slide",
            subtitle="Supporting",
            body_text="This is body text that will be overlaid on the image.",
            text_position=TextPosition.CENTER,
            slide_type=SlideType.CONTENT,
        )
        gen_image = _make_png()
        result = renderer.render(slide=slide, generated_image=gen_image)
        # Result should be different from input (overlay was applied)
        assert result != gen_image
        # Result should be a valid PNG with correct dimensions
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    def test_overlay_bottom_position(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=2,
            heading="Bottom Text",
            subtitle="",
            body_text="Body at bottom.",
            text_position=TextPosition.BOTTOM,
            slide_type=SlideType.CONTENT,
        )
        gen_image = _make_png()
        result = renderer.render(slide=slide, generated_image=gen_image)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)


class TestFallback:
    def test_fallback_renders_without_image(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=0,
            heading="Fallback Heading",
            subtitle="Fallback subtitle",
            body_text="Fallback body text content.",
            text_position=TextPosition.CENTER,
            slide_type=SlideType.CONTENT,
        )
        result = renderer.render(slide=slide, generated_image=None)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    def test_fallback_heading_only(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=0,
            heading="Just a Heading",
            subtitle="",
            body_text="",
            text_position=TextPosition.NONE,
            slide_type=SlideType.HOOK,
        )
        result = renderer.render(slide=slide, generated_image=None)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    def test_fallback_with_all_text_fields(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=1,
            heading="Full Slide",
            subtitle="With subtitle",
            body_text="And body text that is somewhat longer to test wrapping behavior.",
            text_position=TextPosition.CENTER,
            slide_type=SlideType.CONTENT,
        )
        result = renderer.render(slide=slide, generated_image=None)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)
