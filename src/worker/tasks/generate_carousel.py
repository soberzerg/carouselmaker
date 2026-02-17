from __future__ import annotations

import asyncio
import logging

from src.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _generate_carousel(
    user_id: int,
    telegram_chat_id: int,
    input_text: str,
    style_slug: str,
    status_message_id: int,
) -> None:
    """Async pipeline: AI copy → AI image → render → S3 → send to Telegram."""
    from src.services.carousel_service import CarouselService

    service = CarouselService()
    await service.generate_and_send(
        user_id=user_id,
        telegram_chat_id=telegram_chat_id,
        input_text=input_text,
        style_slug=style_slug,
        status_message_id=status_message_id,
    )


@celery_app.task(name="src.worker.tasks.generate_carousel.generate_carousel_task", bind=True)
def generate_carousel_task(
    self,  # type: ignore[no-untyped-def]
    user_id: int,
    telegram_chat_id: int,
    input_text: str,
    style_slug: str,
    status_message_id: int,
) -> dict[str, str]:
    """Sync Celery task wrapping the async pipeline."""
    logger.info("Starting carousel generation for user %d", user_id)
    try:
        asyncio.run(
            _generate_carousel(
                user_id=user_id,
                telegram_chat_id=telegram_chat_id,
                input_text=input_text,
                style_slug=style_slug,
                status_message_id=status_message_id,
            )
        )
        return {"status": "completed"}
    except Exception as e:
        logger.exception("Carousel generation failed for user %d: %s", user_id, e)
        return {"status": "failed", "error": str(e)}
