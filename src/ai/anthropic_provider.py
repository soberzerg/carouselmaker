from __future__ import annotations

import json
import logging
import re

import anthropic

from src.ai.base import CopywriterProvider
from src.ai.template_loader import render_prompt
from src.config.settings import get_settings
from src.schemas.slide import (
    ComparisonBlock,
    ComparisonData,
    ContentTemplate,
    ListingData,
    QuoteData,
    SlideContent,
    SlideType,
    StatsData,
    StepItem,
    StepsData,
    TextPosition,
)

logger = logging.getLogger(__name__)


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```) from AI response."""
    return re.sub(r"^```(?:json)?\s*\n?|\n?```\s*$", "", text.strip())


def _parse_slide(raw: dict[str, object]) -> SlideContent:
    """Parse a single slide dict from Claude, handling template-specific fields."""
    # Extract template-specific fields before passing to SlideContent
    listing_items = raw.pop("listing_items", None)
    comparison_raw = raw.pop("comparison_data", None)
    quote_raw = raw.pop("quote_data", None)
    stats_raw = raw.pop("stats_data", None)
    steps_raw = raw.pop("steps_data", None)

    slide = SlideContent(**raw)

    # Transform listing items into ListingData
    if listing_items and slide.content_template == ContentTemplate.LISTING:
        slide.listing_data = ListingData(items=listing_items)

    # Transform comparison dict into ComparisonData
    if (
        isinstance(comparison_raw, dict)
        and slide.content_template == ContentTemplate.COMPARISON
    ):
        try:
            slide.comparison_data = ComparisonData(
                top_block=ComparisonBlock(**comparison_raw["top_block"]),
                bottom_block=ComparisonBlock(**comparison_raw["bottom_block"]),
            )
        except (KeyError, TypeError):
            logger.warning(
                "Invalid comparison_data for slide %d, falling back to text",
                slide.position,
            )
            slide.content_template = ContentTemplate.TEXT
            slide.comparison_data = None

    # Transform quote dict into QuoteData
    if isinstance(quote_raw, dict) and slide.content_template == ContentTemplate.QUOTE:
        try:
            slide.quote_data = QuoteData(**quote_raw)
        except (TypeError, ValueError):
            logger.warning("Invalid quote_data for slide %d, falling back to text", slide.position)
            slide.content_template = ContentTemplate.TEXT
            slide.quote_data = None

    # Transform stats dict into StatsData
    if isinstance(stats_raw, dict) and slide.content_template == ContentTemplate.STATS:
        try:
            slide.stats_data = StatsData(**stats_raw)
        except (TypeError, ValueError):
            logger.warning("Invalid stats_data for slide %d, falling back to text", slide.position)
            slide.content_template = ContentTemplate.TEXT
            slide.stats_data = None

    # Transform steps dict into StepsData
    if isinstance(steps_raw, dict) and slide.content_template == ContentTemplate.STEPS:
        try:
            items = [StepItem(**item) for item in steps_raw.get("items", [])]
            slide.steps_data = StepsData(items=items)
        except (TypeError, ValueError, KeyError):
            logger.warning("Invalid steps_data for slide %d, falling back to text", slide.position)
            slide.content_template = ContentTemplate.TEXT
            slide.steps_data = None

    # If listing template but no items, fall back to text
    if slide.content_template == ContentTemplate.LISTING and not slide.listing_data:
        slide.content_template = ContentTemplate.TEXT

    # If comparison template but no data, fall back to text
    if slide.content_template == ContentTemplate.COMPARISON and not slide.comparison_data:
        slide.content_template = ContentTemplate.TEXT

    # If quote template but no data, fall back to text
    if slide.content_template == ContentTemplate.QUOTE and not slide.quote_data:
        slide.content_template = ContentTemplate.TEXT

    # If stats template but no data, fall back to text
    if slide.content_template == ContentTemplate.STATS and not slide.stats_data:
        slide.content_template = ContentTemplate.TEXT

    # If steps template but no data, fall back to text
    if slide.content_template == ContentTemplate.STEPS and not slide.steps_data:
        slide.content_template = ContentTemplate.TEXT

    return slide


class AnthropicCopywriter(CopywriterProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic.api_key.get_secret_value(),
            timeout=120.0,
        )
        self.model = settings.anthropic.model
        self.max_tokens = settings.anthropic.max_tokens

    async def generate_slides(
        self,
        input_text: str,
        style_slug: str,
        slide_count: int,
    ) -> list[SlideContent]:
        user_prompt = render_prompt(
            "copywriter_user.mako",
            style_slug=style_slug,
            slide_count=slide_count,
            input_text=input_text,
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=render_prompt("copywriter_system.mako"),
            messages=[{"role": "user", "content": user_prompt}],
        )

        if not response.content:
            raise ValueError("Claude returned empty response content")

        raw_text = response.content[0].text  # type: ignore[union-attr]
        logger.debug("Claude response: %s", raw_text)

        cleaned = _strip_markdown_fences(raw_text)
        try:
            slides_data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude response as JSON: %s", raw_text[:500])
            raise ValueError(f"AI returned invalid JSON: {e}") from e

        slides = [_parse_slide(s) for s in slides_data]

        # Enforce slide types: first = hook, last = cta
        if slides:
            slides[0].slide_type = SlideType.HOOK
            if slides[0].text_position != TextPosition.NONE and not slides[0].body_text:
                slides[0].text_position = TextPosition.NONE
        if len(slides) > 1:
            slides[-1].slide_type = SlideType.CTA

        # Enforce: non-content slides always use text template
        for s in slides:
            if s.slide_type != SlideType.CONTENT:
                s.content_template = ContentTemplate.TEXT
                s.listing_data = None
                s.comparison_data = None
                s.quote_data = None
                s.stats_data = None
                s.steps_data = None

        # Assign slide numbers (1-based for content slides)
        content_counter = 0
        for s in slides:
            if s.slide_type == SlideType.CONTENT:
                content_counter += 1
                s.slide_number = content_counter

        return slides
