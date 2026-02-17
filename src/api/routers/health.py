from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readiness")
async def readiness(
    session: AsyncSession = Depends(get_db_session),  # noqa: B008
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}
