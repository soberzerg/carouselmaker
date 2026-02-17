from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from src.config.constants import S3_CAROUSEL_PREFIX, S3_CLEANUP_DAYS
from src.storage.s3 import S3Client
from src.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.worker.tasks.cleanup.cleanup_old_files")
def cleanup_old_files() -> dict[str, int]:
    """Periodic task: remove S3 files older than S3_CLEANUP_DAYS."""
    s3 = S3Client()
    cutoff = datetime.now(UTC) - timedelta(days=S3_CLEANUP_DAYS)
    deleted = 0

    keys = s3.list_objects(prefix=S3_CAROUSEL_PREFIX)
    for key in keys:
        # Keys are formatted as: carousels/{user_id}/{carousel_id}/{timestamp}_slide_{n}.png
        try:
            parts = key.split("/")
            # Extract timestamp from filename
            filename = parts[-1]
            ts_str = filename.split("_")[0]
            ts = datetime.fromtimestamp(int(ts_str), tz=UTC)
            if ts < cutoff:
                s3.delete_object(key)
                deleted += 1
        except (IndexError, ValueError):
            continue

    logger.info("Cleanup: deleted %d old files", deleted)
    return {"deleted": deleted}
