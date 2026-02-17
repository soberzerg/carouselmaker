from __future__ import annotations

import json
import logging

import anthropic

from src.ai.base import CopywriterProvider
from src.ai.prompts import COPYWRITER_SYSTEM_PROMPT, COPYWRITER_USER_PROMPT
from src.config.settings import get_settings
from src.schemas.slide import SlideContent

logger = logging.getLogger(__name__)


class AnthropicCopywriter(CopywriterProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic.api_key.get_secret_value()
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

        raw_text = response.content[0].text  # type: ignore[union-attr]
        logger.debug("Claude response: %s", raw_text)

        slides_data = json.loads(raw_text)
        return [SlideContent(**s) for s in slides_data]
