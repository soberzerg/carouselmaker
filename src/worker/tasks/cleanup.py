from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from src.config.constants import S3_CAROUSEL_PREFIX, S3_CLEANUP_DAYS
from src.db.session import get_session_factory
from src.models.slide import Slide
from src.storage.s3 import S3Client
from src.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _null_out_s3_keys(s3_keys: list[str]) -> None:
    """Null out rendered_s3_key for deleted S3 files in the database."""
    if not s3_keys:
        return
    factory = get_session_factory()
    async with factory() as session:
        stmt = update(Slide).where(Slide.rendered_s3_key.in_(s3_keys)).values(rendered_s3_key=None)
        await session.execute(stmt)
        await session.commit()


@celery_app.task(  # type: ignore[untyped-decorator]
    name="src.worker.tasks.cleanup.cleanup_old_files",
    max_retries=3,
    default_retry_delay=300,
)
def cleanup_old_files() -> dict[str, int]:
    """Periodic task: remove S3 files older than S3_CLEANUP_DAYS."""
    s3 = S3Client()
    cutoff = datetime.now(UTC) - timedelta(days=S3_CLEANUP_DAYS)
    deleted = 0
    deleted_keys: list[str] = []

    keys = s3.list_objects(prefix=S3_CAROUSEL_PREFIX)
    for key in keys:
        # Keys are formatted as: carousels/{user_id}/{carousel_id}/{timestamp}_slide_{n}.png
        try:
            parts = key.split("/")
            if len(parts) < 4:
                continue
            # Extract timestamp from filename
            filename = parts[-1]
            ts_parts = filename.split("_")
            if not ts_parts:
                continue
            ts_str = ts_parts[0]
            ts = datetime.fromtimestamp(int(ts_str), tz=UTC)
            if ts < cutoff:
                s3.delete_object(key)
                deleted_keys.append(key)
                deleted += 1
        except (IndexError, ValueError):
            continue

    # Null out S3 keys in database for deleted files
    if deleted_keys:
        asyncio.run(_null_out_s3_keys(deleted_keys))

    logger.info("Cleanup: deleted %d old files", deleted)
    return {"deleted": deleted}
