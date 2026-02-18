from __future__ import annotations

import pytest

from src.ai.template_loader import render_prompt
from src.schemas.slide import SlideType, TextPosition


class TestRenderPrompt:
    def test_static_template_renders(self) -> None:
        result = render_prompt("copywriter_system.mako")
        assert "expert copywriter" in result
        assert "JSON array" in result

    def test_copywriter_user_substitution(self) -> None:
        result = render_prompt(
            "copywriter_user.mako",
            style_slug="nano_banana",
            slide_count=5,
            input_text="Hello world",
        )
        assert "Style: nano_banana" in result
        assert "Number of slides: 5" in result
        assert "Hello world" in result

    def test_missing_variable_raises(self) -> None:
        with pytest.raises(NameError):
            render_prompt("copywriter_user.mako", style_slug="x")

    def test_nonexistent_template_raises(self) -> None:
        from mako.exceptions import TopLevelLookupException

        with pytest.raises(TopLevelLookupException):
            render_prompt("does_not_exist.mako")


class TestSlideImageTemplate:
    def _render(self, slide_type: str = "content", text_position: str = "none") -> str:
        return render_prompt(
            "slide_image_prompt.mako",
            heading="Test",
            subtitle="Sub",
            style_name="Style",
            style_mood="clean",
            style_description="desc",
            bg_color="#000",
            text_color="#FFF",
            accent_color="#F00",
            visual_hints="",
            slide_type=slide_type,
            text_position=text_position,
        )

    def test_hook_slide_type(self) -> None:
        result = self._render(slide_type="hook")
        assert "HOOK slide" in result

    def test_content_slide_type(self) -> None:
        result = self._render(slide_type="content")
        assert "CONTENT slide" in result

    def test_cta_slide_type(self) -> None:
        result = self._render(slide_type="cta")
        assert "CTA" in result

    def test_center_text_position(self) -> None:
        result = self._render(text_position="center")
        assert "upper portion" in result
        assert "center of the slide" in result

    def test_bottom_text_position(self) -> None:
        result = self._render(text_position="bottom")
        assert "upper half" in result
        assert "bottom third" in result

    def test_none_text_position(self) -> None:
        result = self._render(text_position="none")
        assert "main visual focus" in result
        assert "No clean zone needed" in result

    def test_all_slide_types(self) -> None:
        for st in SlideType:
            result = self._render(slide_type=st.value)
            assert len(result) > 100

    def test_all_text_positions(self) -> None:
        for tp in TextPosition:
            result = self._render(text_position=tp.value)
            assert len(result) > 100
