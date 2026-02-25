from __future__ import annotations

import asyncio
import logging
import threading

from src.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persistent event loop shared across all tasks in this worker process.
# Celery runs synchronous tasks, so we maintain a single background thread
# with its own event loop instead of calling asyncio.run() per task (which
# creates/destroys a loop every time and breaks asyncpg connection pooling).
# ---------------------------------------------------------------------------
_loop: asyncio.AbstractEventLoop | None = None
_loop_lock = threading.Lock()


def _get_event_loop() -> asyncio.AbstractEventLoop:
    global _loop  # noqa: PLW0603
    if _loop is not None and _loop.is_running():
        return _loop
    with _loop_lock:
        if _loop is not None and _loop.is_running():
            return _loop
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=loop.run_forever, daemon=True)
        thread.start()
        _loop = loop
        return _loop


async def _generate_carousel(
    user_id: int,
    telegram_chat_id: int,
    input_text: str,
    style_slug: str,
    status_message_id: int,
    celery_task_id: str,
) -> None:
    """Async pipeline: AI copy -> AI image -> render -> S3 -> send to Telegram."""
    from sqlalchemy import select

    from src.db.session import get_session_factory
    from src.models.carousel import CarouselGeneration, GenerationStatus
    from src.services.carousel_service import CarouselService

    # Idempotency guard: if a previous attempt already completed, skip.
    factory = get_session_factory()
    async with factory() as session:
        existing = (
            await session.execute(
                select(CarouselGeneration).where(
                    CarouselGeneration.celery_task_id == celery_task_id,
                    CarouselGeneration.status == GenerationStatus.COMPLETED,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            logger.info(
                "Task %s already completed (generation %d), skipping duplicate",
                celery_task_id,
                existing.id,
            )
            return

    service = CarouselService()
    await service.generate_and_send(
        user_id=user_id,
        telegram_chat_id=telegram_chat_id,
        input_text=input_text,
        style_slug=style_slug,
        status_message_id=status_message_id,
        celery_task_id=celery_task_id,
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
        loop = _get_event_loop()
        future = asyncio.run_coroutine_threadsafe(
            _generate_carousel(
                user_id=user_id,
                telegram_chat_id=telegram_chat_id,
                input_text=input_text,
                style_slug=style_slug,
                status_message_id=status_message_id,
                celery_task_id=self.request.id,
            ),
            loop,
        )
        future.result()  # blocks until coroutine completes
        return {"status": "completed"}
    except Exception as e:
        logger.exception("Carousel generation failed for user %d: %s", user_id, e)
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for user %d", user_id)
        raise
