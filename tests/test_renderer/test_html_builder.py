from __future__ import annotations

from src.renderer.html_builder import (
    build_comparison_html,
    build_listing_html,
    build_quote_html,
    build_stats_html,
    build_text_html,
)
from src.renderer.styles import StyleConfig
from src.schemas.slide import (
    ComparisonBlock,
    ComparisonData,
    ContentTemplate,
    ListingData,
    QuoteData,
    SlideContent,
    StatsData,
    StepItem,
    StepsData,
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


class TestBuildQuoteHtml:
    def test_contains_quote_text(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Wisdom",
            content_template=ContentTemplate.QUOTE,
            quote_data=QuoteData(
                quote_text="Stay hungry, stay foolish",
                author_name="Steve Jobs",
                author_title="Apple CEO",
            ),
        )
        html = build_quote_html(slide, _make_style())
        assert "Stay hungry, stay foolish" in html
        assert "Steve Jobs" in html
        assert "Apple CEO" in html

    def test_works_without_author_title(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Quote",
            content_template=ContentTemplate.QUOTE,
            quote_data=QuoteData(
                quote_text="Just do it",
                author_name="Nike",
            ),
        )
        html = build_quote_html(slide, _make_style())
        assert "Just do it" in html
        assert "Nike" in html

    def test_slide_number_rendered(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Quote",
            content_template=ContentTemplate.QUOTE,
            quote_data=QuoteData(
                quote_text="Test quote",
                author_name="Author",
            ),
            slide_number=2,
        )
        html = build_quote_html(slide, _make_style())
        assert "02" in html


class TestBuildStatsHtml:
    def test_contains_value_and_label(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Our Growth",
            content_template=ContentTemplate.STATS,
            stats_data=StatsData(
                value="340%",
                label="growth in 3 months",
                context="Year over year comparison",
            ),
        )
        html = build_stats_html(slide, _make_style())
        assert "340%" in html
        assert "growth in 3 months" in html
        assert "Year over year comparison" in html
        assert "Our Growth" in html

    def test_works_without_context(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Metric",
            content_template=ContentTemplate.STATS,
            stats_data=StatsData(value="$2.5M", label="revenue"),
        )
        html = build_stats_html(slide, _make_style())
        assert "$2.5M" in html
        assert "revenue" in html

    def test_slide_number_rendered(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Stats",
            content_template=ContentTemplate.STATS,
            stats_data=StatsData(value="10K+", label="users"),
            slide_number=4,
        )
        html = build_stats_html(slide, _make_style())
        assert "04" in html


class TestQuoteDataModel:
    def test_quote_data_creation(self) -> None:
        q = QuoteData(quote_text="Stay hungry", author_name="Steve Jobs", author_title="Apple CEO")
        assert q.quote_text == "Stay hungry"
        assert q.author_name == "Steve Jobs"
        assert q.author_title == "Apple CEO"

    def test_quote_data_optional_title(self) -> None:
        q = QuoteData(quote_text="Test", author_name="Author")
        assert q.author_title == ""


class TestStatsDataModel:
    def test_stats_data_creation(self) -> None:
        s = StatsData(value="340%", label="growth in 3 months", context="Year over year")
        assert s.value == "340%"
        assert s.label == "growth in 3 months"
        assert s.context == "Year over year"

    def test_stats_data_optional_context(self) -> None:
        s = StatsData(value="10K+", label="users")
        assert s.context == ""


class TestStepsDataModel:
    def test_steps_data_creation(self) -> None:
        items = [
            StepItem(title="Step 1", description="Do this"),
            StepItem(title="Step 2", description="Then this"),
        ]
        sd = StepsData(items=items)
        assert len(sd.items) == 2
        assert sd.items[0].title == "Step 1"

    def test_step_item_optional_description(self) -> None:
        item = StepItem(title="Just a title")
        assert item.description == ""
