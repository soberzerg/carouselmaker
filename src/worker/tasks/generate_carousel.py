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
    """Async pipeline: AI copy -> AI image -> render -> S3 -> send to Telegram."""
    from src.db.session import get_engine
    from src.services.carousel_service import CarouselService

    # Dispose stale connections from previous event loops.
    # Each asyncio.run() creates a new loop, but the cached engine's pool
    # may hold connections bound to the old loop, causing
    # "another operation is in progress" errors from asyncpg.
    await get_engine().dispose()

    service = CarouselService()
    await service.generate_and_send(
        user_id=user_id,
        telegram_chat_id=telegram_chat_id,
        input_text=input_text,
        style_slug=style_slug,
        status_message_id=status_message_id,
    )


@celery_app.task(  # type: ignore[untyped-decorator]
    name="src.worker.tasks.generate_carousel.generate_carousel_task",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_carousel_task(  # type: ignore[no-untyped-def]
    self,  # noqa: ANN001
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
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for user %d", user_id)
        raise
