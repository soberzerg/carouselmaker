from __future__ import annotations

import logging

from google import genai

from src.ai.base import ImageProvider
from src.ai.prompts import IMAGE_PROMPT_TEMPLATE
from src.config.settings import get_settings
from src.renderer.styles import STYLE_DESCRIPTIONS

logger = logging.getLogger(__name__)


class GeminiImageProvider(ImageProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini.api_key.get_secret_value())
        self.model = settings.gemini.model

    async def generate_background(
        self,
        style_slug: str,
        slide_heading: str,
        slide_position: int,
    ) -> bytes:
        style_desc = STYLE_DESCRIPTIONS.get(style_slug, "modern and clean")
        prompt = IMAGE_PROMPT_TEMPLATE.format(
            style_description=style_desc,
            slide_heading=slide_heading,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        # If the model returns an image, extract bytes
        # Gemini image generation returns inline_data for images
        for part in response.candidates[0].content.parts:  # type: ignore[union-attr]
            if hasattr(part, "inline_data") and part.inline_data:
                return part.inline_data.data  # type: ignore[return-value]

        # Fallback: return empty bytes (renderer will use solid color)
        logger.warning("Gemini did not return an image for slide %d", slide_position)
        return b""
