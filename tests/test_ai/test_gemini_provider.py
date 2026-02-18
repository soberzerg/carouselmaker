from __future__ import annotations

import io

from PIL import Image

from src.ai.prompts import (
    CLEAN_ZONE_INSTRUCTIONS,
    SLIDE_IMAGE_PROMPT_TEMPLATE,
    SLIDE_TYPE_INSTRUCTIONS,
    TEXT_AREA_DESCRIPTIONS,
)
from src.config.constants import SLIDE_HEIGHT, SLIDE_WIDTH
from src.renderer.styles import StyleConfig
from src.schemas.slide import SlideContent, SlideType, TextPosition


def _make_style() -> StyleConfig:
    return StyleConfig(
        slug="nano_banana",
        name="Nano Banana",
        bg_color="#1A1A1A",
        text_color="#FFFFFF",
        accent_color="#FFD600",
        extra={
            "mood": "bold, energetic",
            "description": "High-contrast yellow on black",
            "visual_prompt_hints": "Use dramatic black backgrounds",
        },
    )


class TestPromptConstruction:
    def test_prompt_template_formats_correctly(self) -> None:
        style = _make_style()
        slide = SlideContent(
            position=0,
            heading="Test Heading",
            subtitle="Test Subtitle",
            text_position=TextPosition.NONE,
            slide_type=SlideType.HOOK,
        )
        prompt = SLIDE_IMAGE_PROMPT_TEMPLATE.format(
            heading=slide.heading,
            subtitle=slide.subtitle,
            style_name=style.name,
            style_mood=style.extra.get("mood", ""),
            style_description=style.extra.get("description", ""),
            bg_color=style.bg_color,
            text_color=style.text_color,
            accent_color=style.accent_color,
            visual_hints="Visual hints: Use dramatic black backgrounds",
            text_area_description=TEXT_AREA_DESCRIPTIONS["none"],
            slide_type_instruction=SLIDE_TYPE_INSTRUCTIONS["hook"],
            clean_zone_instruction=CLEAN_ZONE_INSTRUCTIONS["none"],
        )
        assert "Test Heading" in prompt
        assert "Test Subtitle" in prompt
        assert "Nano Banana" in prompt
        assert "#FFD600" in prompt
        assert "HOOK" in prompt

    def test_all_slide_types_have_instructions(self) -> None:
        for st in SlideType:
            assert st.value in SLIDE_TYPE_INSTRUCTIONS

    def test_all_text_positions_have_descriptions(self) -> None:
        for tp in TextPosition:
            assert tp.value in TEXT_AREA_DESCRIPTIONS
            assert tp.value in CLEAN_ZONE_INSTRUCTIONS


class TestImageValidation:
    """Test the _validate_image static logic (extracted for unit testing)."""

    def test_valid_png_passes_through(self) -> None:
        from src.ai.gemini_provider import GeminiImageProvider

        provider = GeminiImageProvider.__new__(GeminiImageProvider)
        img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), (0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()

        result = provider._validate_image(data, 0)
        assert result is not None
        validated = Image.open(io.BytesIO(result))
        assert validated.size == (SLIDE_WIDTH, SLIDE_HEIGHT)

    def test_wrong_dimensions_get_resized(self) -> None:
        from src.ai.gemini_provider import GeminiImageProvider

        provider = GeminiImageProvider.__new__(GeminiImageProvider)
        img = Image.new("RGB", (800, 600), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()

        result = provider._validate_image(data, 0)
        assert result is not None
        validated = Image.open(io.BytesIO(result))
        assert validated.size == (SLIDE_WIDTH, SLIDE_HEIGHT)

    def test_rgba_converted_to_rgb(self) -> None:
        from src.ai.gemini_provider import GeminiImageProvider

        provider = GeminiImageProvider.__new__(GeminiImageProvider)
        img = Image.new("RGBA", (SLIDE_WIDTH, SLIDE_HEIGHT), (0, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()

        result = provider._validate_image(data, 0)
        assert result is not None
        validated = Image.open(io.BytesIO(result))
        assert validated.mode == "RGB"

    def test_invalid_data_returns_none(self) -> None:
        from src.ai.gemini_provider import GeminiImageProvider

        provider = GeminiImageProvider.__new__(GeminiImageProvider)
        result = provider._validate_image(b"not an image", 0)
        assert result is None
