from __future__ import annotations

import json
import logging
import re

import anthropic

from src.ai.base import CopywriterProvider
from src.ai.prompts import COPYWRITER_SYSTEM_PROMPT, COPYWRITER_USER_PROMPT
from src.config.settings import get_settings
from src.schemas.slide import SlideContent

logger = logging.getLogger(__name__)


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```) from AI response."""
    return re.sub(r"^```(?:json)?\s*\n?|\n?```\s*$", "", text.strip())


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
        user_prompt = COPYWRITER_USER_PROMPT.format(
            style_slug=style_slug,
            slide_count=slide_count,
            input_text=input_text,
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=COPYWRITER_SYSTEM_PROMPT,
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

        return [SlideContent(**s) for s in slides_data]
