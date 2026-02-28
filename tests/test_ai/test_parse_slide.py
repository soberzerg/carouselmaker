from __future__ import annotations

from src.ai.anthropic_provider import _parse_slide
from src.schemas.slide import ContentTemplate


class TestParseSlideNewTemplates:
    def test_parse_quote_slide(self) -> None:
        raw = {
            "position": 2,
            "heading": "Wisdom",
            "subtitle": "",
            "body_text": "",
            "text_position": "none",
            "slide_type": "content",
            "image_description": "",
            "content_template": "quote",
            "quote_data": {
                "quote_text": "Stay hungry",
                "author_name": "Steve Jobs",
                "author_title": "Apple CEO",
            },
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.QUOTE
        assert slide.quote_data is not None
        assert slide.quote_data.quote_text == "Stay hungry"
        assert slide.quote_data.author_name == "Steve Jobs"

    def test_parse_stats_slide(self) -> None:
        raw = {
            "position": 3,
            "heading": "Growth",
            "subtitle": "",
            "body_text": "",
            "text_position": "none",
            "slide_type": "content",
            "image_description": "",
            "content_template": "stats",
            "stats_data": {
                "value": "340%",
                "label": "growth",
                "context": "",
            },
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.STATS
        assert slide.stats_data is not None
        assert slide.stats_data.value == "340%"

    def test_parse_steps_slide(self) -> None:
        raw = {
            "position": 4,
            "heading": "How to Start",
            "subtitle": "",
            "body_text": "",
            "text_position": "none",
            "slide_type": "content",
            "image_description": "",
            "content_template": "steps",
            "steps_data": {
                "items": [
                    {"title": "Plan", "description": "Make a plan"},
                    {"title": "Execute", "description": ""},
                ],
            },
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.STEPS
        assert slide.steps_data is not None
        assert len(slide.steps_data.items) == 2

    def test_quote_without_data_falls_back_to_text(self) -> None:
        raw = {
            "position": 2,
            "heading": "Bad Quote",
            "subtitle": "",
            "body_text": "fallback",
            "text_position": "center",
            "slide_type": "content",
            "image_description": "",
            "content_template": "quote",
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.TEXT
        assert slide.quote_data is None

    def test_stats_without_data_falls_back_to_text(self) -> None:
        raw = {
            "position": 3,
            "heading": "Bad Stats",
            "subtitle": "",
            "body_text": "fallback",
            "text_position": "center",
            "slide_type": "content",
            "image_description": "",
            "content_template": "stats",
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.TEXT

    def test_steps_without_data_falls_back_to_text(self) -> None:
        raw = {
            "position": 4,
            "heading": "Bad Steps",
            "subtitle": "",
            "body_text": "fallback",
            "text_position": "center",
            "slide_type": "content",
            "image_description": "",
            "content_template": "steps",
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.TEXT
