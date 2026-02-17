from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from src.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "carouselmaker",
    broker=settings.redis.url,
    backend=settings.redis.url,
)

celery_app.conf.update(
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

celery_app.autodiscover_tasks(["src.worker.tasks"])
