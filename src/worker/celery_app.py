from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from src.config.settings import get_settings


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
