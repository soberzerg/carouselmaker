from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.slide import SlideContent, SlideType, TextPosition
from src.services.carousel_service import CarouselService, TelegramNotifier, _ProgressCounter


class TestTelegramNotifier:
    @pytest.mark.asyncio
    async def test_update_sends_message(self) -> None:
        with patch("src.services.carousel_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.post = AsyncMock()

            notifier = TelegramNotifier("token", 123, 456)
            await notifier.update("Test message")

            mock_client.post.assert_called_once()
            await notifier.close()

    @pytest.mark.asyncio
    async def test_update_skips_duplicate_message(self) -> None:
        with patch("src.services.carousel_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.post = AsyncMock()

            notifier = TelegramNotifier("token", 123, 456)
            await notifier.update("Same message")
            await notifier.update("Same message")

            # Should only be called once since message didn't change
            assert mock_client.post.call_count == 1
            await notifier.close()


class TestGenerateSlideImageWithRetry:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self) -> None:
        service = CarouselService.__new__(CarouselService)
        service.image_provider = MagicMock()
        service.image_provider.generate_slide_image = AsyncMock(return_value=b"png_data")

        slide = SlideContent(
            position=0,
            heading="Test",
            text_position=TextPosition.NONE,
            slide_type=SlideType.HOOK,
        )

        notifier = AsyncMock(spec=TelegramNotifier)
        notifier.update = AsyncMock()

        result = await service._generate_slide_image_with_retry(
            slide=slide,
            style_config=MagicMock(),
            semaphore=asyncio.Semaphore(3),
            notifier=notifier,
            total=5,
            progress=_ProgressCounter(),
        )

        assert result == b"png_data"
        assert service.image_provider.generate_slide_image.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure_then_succeeds(self) -> None:
        service = CarouselService.__new__(CarouselService)
        service.image_provider = MagicMock()
        service.image_provider.generate_slide_image = AsyncMock(side_effect=[None, b"png_data"])

        slide = SlideContent(
            position=1,
            heading="Retry Test",
            text_position=TextPosition.CENTER,
            slide_type=SlideType.CONTENT,
        )

        notifier = AsyncMock(spec=TelegramNotifier)
        notifier.update = AsyncMock()

        result = await service._generate_slide_image_with_retry(
            slide=slide,
            style_config=MagicMock(),
            semaphore=asyncio.Semaphore(3),
            notifier=notifier,
            total=5,
            progress=_ProgressCounter(),
        )

        assert result == b"png_data"
        assert service.image_provider.generate_slide_image.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_none_after_all_retries_exhausted(self) -> None:
        service = CarouselService.__new__(CarouselService)
        service.image_provider = MagicMock()
        service.image_provider.generate_slide_image = AsyncMock(return_value=None)

        slide = SlideContent(
            position=2,
            heading="Fail",
            text_position=TextPosition.NONE,
            slide_type=SlideType.CTA,
        )

        notifier = AsyncMock(spec=TelegramNotifier)
        notifier.update = AsyncMock()

        result = await service._generate_slide_image_with_retry(
            slide=slide,
            style_config=MagicMock(),
            semaphore=asyncio.Semaphore(3),
            notifier=notifier,
            total=5,
            progress=_ProgressCounter(),
        )

        assert result is None
        # 1 initial + 2 retries = 3 total attempts
        assert service.image_provider.generate_slide_image.call_count == 3
