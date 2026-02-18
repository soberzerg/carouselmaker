from __future__ import annotations

from abc import ABC, abstractmethod

from src.renderer.styles import StyleConfig
from src.schemas.slide import SlideContent


class CopywriterProvider(ABC):
    @abstractmethod
    async def generate_slides(
        self,
        input_text: str,
        style_slug: str,
        slide_count: int,
    ) -> list[SlideContent]:
        """Generate slide content from user text."""
        ...


class ImageProvider(ABC):
    @abstractmethod
    async def generate_slide_image(
        self,
        slide: SlideContent,
        style_config: StyleConfig,
    ) -> bytes | None:
        """Generate a complete slide image with heading/subtitle baked in.

        Returns PNG bytes on success, or None if image generation fails.
        """
        ...
