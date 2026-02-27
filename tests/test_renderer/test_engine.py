from __future__ import annotations

import io

import pytest
from PIL import Image

from src.config.constants import SLIDE_HEIGHT, SLIDE_WIDTH
from src.renderer.engine import SlideRenderer
from src.renderer.styles import StyleConfig
from src.schemas.slide import (
    ComparisonBlock,
    ComparisonData,
    ContentTemplate,
    ListingData,
    SlideContent,
    SlideType,
    TextPosition,
)


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


@pytest.fixture(autouse=True)
async def _cleanup_browser() -> None:  # type: ignore[misc]
    """Ensure browser is shut down after tests."""
    yield  # type: ignore[misc]
    from src.renderer.browser import shutdown

    await shutdown()


class TestPassthrough:
    async def test_returns_image_as_is_when_no_body_text(self) -> None:
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
        result = await renderer.render(slide=slide, generated_image=gen_image)
        assert result == gen_image

    async def test_returns_image_as_is_when_text_position_none(self) -> None:
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
        result = await renderer.render(slide=slide, generated_image=gen_image)
        # text_position=none means passthrough even if body_text exists
        assert result == gen_image


class TestOverlay:
    async def test_overlay_produces_valid_png(self) -> None:
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
        result = await renderer.render(
            slide=slide, generated_image=gen_image,
        )
        # Result should be different from input (overlay was applied)
        assert result != gen_image
        # Result should be a valid PNG with correct dimensions
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    async def test_overlay_bottom_position(self) -> None:
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
        result = await renderer.render(
            slide=slide, generated_image=gen_image,
        )
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)


class TestContentTemplates:
    async def test_text_template_renders(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=1,
            heading="Text Heading",
            subtitle="Subtitle",
            body_text="Body text content.",
            text_position=TextPosition.CENTER,
            slide_type=SlideType.CONTENT,
            content_template=ContentTemplate.TEXT,
            slide_number=1,
        )
        result = await renderer.render(slide=slide)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    async def test_listing_template_renders(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=2,
            heading="Listing Heading",
            subtitle="Key points",
            slide_type=SlideType.CONTENT,
            content_template=ContentTemplate.LISTING,
            listing_data=ListingData(items=["First", "Second", "Third"]),
            slide_number=2,
        )
        result = await renderer.render(slide=slide)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    async def test_comparison_template_renders(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=3,
            heading="VS Comparison",
            subtitle="Side by side",
            slide_type=SlideType.CONTENT,
            content_template=ContentTemplate.COMPARISON,
            comparison_data=ComparisonData(
                top_block=ComparisonBlock(
                    label="Option A", items=["Fast", "Cheap"],
                ),
                bottom_block=ComparisonBlock(
                    label="Option B", items=["Slow", "Expensive"],
                ),
            ),
            slide_number=3,
        )
        result = await renderer.render(slide=slide)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)


class TestFallback:
    async def test_fallback_renders_without_image(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=0,
            heading="Fallback Heading",
            subtitle="Fallback subtitle",
            body_text="Fallback body text content.",
            text_position=TextPosition.CENTER,
            slide_type=SlideType.CONTENT,
        )
        result = await renderer.render(slide=slide, generated_image=None)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    async def test_fallback_heading_only(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=0,
            heading="Just a Heading",
            subtitle="",
            body_text="",
            text_position=TextPosition.NONE,
            slide_type=SlideType.HOOK,
        )
        result = await renderer.render(slide=slide, generated_image=None)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    async def test_fallback_with_all_text_fields(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=1,
            heading="Full Slide",
            subtitle="With subtitle",
            body_text="And body text for wrapping behavior.",
            text_position=TextPosition.CENTER,
            slide_type=SlideType.CONTENT,
        )
        result = await renderer.render(
            slide=slide, generated_image=None,
        )
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)
