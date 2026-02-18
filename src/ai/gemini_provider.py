from __future__ import annotations

import io
import logging

from google import genai
from google.genai import types
from PIL import Image

from src.ai.base import ImageProvider
from src.ai.template_loader import render_prompt
from src.config.constants import SLIDE_HEIGHT, SLIDE_WIDTH
from src.config.settings import get_settings
from src.renderer.styles import StyleConfig
from src.schemas.slide import SlideContent

logger = logging.getLogger(__name__)


class GeminiImageProvider(ImageProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini.api_key.get_secret_value())
        self.model = settings.gemini.model

    async def generate_slide_image(
        self,
        slide: SlideContent,
        style_config: StyleConfig,
    ) -> bytes | None:
        extra = style_config.extra
        mood = extra.get("mood", "modern and clean")
        description = extra.get("description", style_config.name)
        visual_hints = extra.get("visual_prompt_hints", "")

        visual_hints_block = f"Visual hints: {visual_hints}" if visual_hints else ""

        prompt = render_prompt(
            "slide_image_prompt.mako",
            heading=slide.heading,
            subtitle=slide.subtitle or "",
            style_name=style_config.name,
            style_mood=mood,
            style_description=description,
            bg_color=style_config.bg_color,
            text_color=style_config.text_color,
            accent_color=style_config.accent_color,
            visual_hints=visual_hints_block,
            text_position=slide.text_position.value,
            slide_type=slide.slide_type.value,
            image_description=slide.image_description,
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
        except Exception:
            logger.exception("Gemini API call failed for slide %d", slide.position)
            return None

        raw_bytes = self._extract_image(response, slide.position)
        if raw_bytes is None:
            return None

        return self._validate_image(raw_bytes, slide.position)

    def _extract_image(self, response: object, position: int) -> bytes | None:
        """Extract image bytes from Gemini response."""
        candidates = getattr(response, "candidates", None)
        if not candidates:
            logger.warning("Gemini returned no candidates for slide %d", position)
            return None

        content = candidates[0].content
        if content and content.parts:
            for part in content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    return part.inline_data.data  # type: ignore[no-any-return]

        logger.warning("Gemini did not return an image for slide %d", position)
        return None

    def _validate_image(self, data: bytes, position: int) -> bytes | None:
        """Validate image data: check format, resize if needed, convert to PNG."""
        try:
            img: Image.Image = Image.open(io.BytesIO(data))
        except Exception:
            logger.warning("Gemini returned invalid image data for slide %d", position)
            return None

        # Resize if dimensions don't match expected size
        if img.size != (SLIDE_WIDTH, SLIDE_HEIGHT):
            logger.debug(
                "Resizing slide %d from %s to %dx%d",
                position,
                img.size,
                SLIDE_WIDTH,
                SLIDE_HEIGHT,
            )
            img = img.resize((SLIDE_WIDTH, SLIDE_HEIGHT), Image.LANCZOS)  # type: ignore[attr-defined]

        # Convert to RGB PNG
        if img.mode != "RGB":
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
