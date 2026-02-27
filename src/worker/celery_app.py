from __future__ import annotations

import asyncio
import logging

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_shutdown

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


def create_celery_app() -> Celery:
    settings = get_settings()

    app = Celery(
        "carouselmaker",
        broker=settings.redis.url,
        backend=settings.redis.url,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        beat_schedule={
            "cleanup-old-files": {
                "task": "src.worker.tasks.cleanup.cleanup_old_files",
                "schedule": crontab(hour=3, minute=0),  # daily at 3 AM
            },
        },
    )

    app.conf.include = [
        "src.worker.tasks.generate_carousel",
        "src.worker.tasks.cleanup",
    ]
    return app


celery_app = create_celery_app()


@worker_shutdown.connect  # type: ignore[untyped-decorator]
def _on_worker_shutdown(**kwargs: object) -> None:
    """Shut down Playwright browser on Celery worker exit."""
    from src.renderer.browser import shutdown

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(shutdown(), loop)
            future.result(timeout=10)
        else:
            asyncio.run(shutdown())
    except Exception:
        logger.debug("Failed to shut down Playwright browser", exc_info=True)
