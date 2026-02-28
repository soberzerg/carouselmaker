from __future__ import annotations

from src.renderer.html_builder import (
    build_comparison_html,
    build_listing_html,
    build_text_html,
)
from src.renderer.styles import StyleConfig
from src.schemas.slide import (
    ComparisonBlock,
    ComparisonData,
    ContentTemplate,
    ListingData,
    SlideContent,
)


def _make_style() -> StyleConfig:
    return StyleConfig(slug="test", name="Test Style")


class TestBuildTextHtml:
    def test_contains_heading(self) -> None:
        slide = SlideContent(
            position=1, heading="Hello World", body_text="Some text",
        )
        html = build_text_html(slide, _make_style())
        assert "Hello World" in html
        assert "Some text" in html

    def test_contains_css_variables(self) -> None:
        style = _make_style()
        slide = SlideContent(position=1, heading="Test")
        html = build_text_html(slide, style)
        assert "--bg-color: #1A1A1A" in html
        assert "--accent-color: #FFD600" in html

    def test_slide_number_rendered(self) -> None:
        slide = SlideContent(
            position=1, heading="Test", slide_number=3,
        )
        html = build_text_html(slide, _make_style())
        assert "03" in html

    def test_no_slide_number_badge_when_none(self) -> None:
        slide = SlideContent(
            position=1, heading="Test", slide_number=None,
        )
        html = build_text_html(slide, _make_style())
        # The CSS class definition exists in base, but no badge div should be rendered
        assert '<div class="slide-number">' not in html


class TestBuildListingHtml:
    def test_contains_items(self) -> None:
        slide = SlideContent(
            position=2,
            heading="Tips",
            content_template=ContentTemplate.LISTING,
            listing_data=ListingData(items=["First", "Second", "Third"]),
        )
        html = build_listing_html(slide, _make_style())
        assert "First" in html
        assert "Second" in html
        assert "Third" in html
        assert "1." in html
        assert "2." in html

    def test_contains_heading(self) -> None:
        slide = SlideContent(
            position=2,
            heading="My Tips",
            content_template=ContentTemplate.LISTING,
            listing_data=ListingData(items=["Item"]),
        )
        html = build_listing_html(slide, _make_style())
        assert "My Tips" in html


class TestBuildComparisonHtml:
    def test_contains_blocks(self) -> None:
        slide = SlideContent(
            position=3,
            heading="Compare",
            content_template=ContentTemplate.COMPARISON,
            comparison_data=ComparisonData(
                top_block=ComparisonBlock(
                    label="Option A",
                    subtitle="The old way",
                    items=["Fast", "Cheap"],
                ),
                bottom_block=ComparisonBlock(
                    label="Option B",
                    subtitle="The new way",
                    items=["Slow", "Expensive"],
                ),
            ),
        )
        html = build_comparison_html(slide, _make_style())
        assert "Option A" in html
        assert "Option B" in html
        assert "The old way" in html
        assert "The new way" in html
        assert "Fast" in html
        assert "Expensive" in html
        assert "VS" in html

    def test_works_without_subtitle(self) -> None:
        slide = SlideContent(
            position=3,
            heading="Compare",
            content_template=ContentTemplate.COMPARISON,
            comparison_data=ComparisonData(
                top_block=ComparisonBlock(
                    label="Before", items=["Point 1"],
                ),
                bottom_block=ComparisonBlock(
                    label="After", items=["Point 2"],
                ),
            ),
        )
        html = build_comparison_html(slide, _make_style())
        assert "Before" in html
        assert "After" in html
        # No subtitle div should be rendered (CSS class definition in style is ok)
        assert '<div class="block-subtitle">' not in html
