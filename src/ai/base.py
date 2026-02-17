from __future__ import annotations

from abc import ABC, abstractmethod

from src.schemas.slide import SlideContent


class CopywriterProvider(ABC):
    @abstractmethod
    async def generate_slides(
        self,
        input_text: str,
        style_slug: str,
        slide_count: int,
    ) -> list[SlideContent]:
        """Generate slide content from user text.

        Implementations should apply a reasonable timeout (e.g. 120s)
        and raise on failure.
        """
        ...


class ImageProvider(ABC):
    @abstractmethod
    async def generate_background(
        self,
        style_slug: str,
        slide_heading: str,
        slide_position: int,
    ) -> bytes | None:
        """Generate a background image for a slide.

        Returns PNG bytes on success, or None if image generation fails.
        Implementations should apply a reasonable timeout and handle
        transient API errors gracefully.
        """
        ...
