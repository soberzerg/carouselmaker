from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session, verify_admin_api_key
from src.models.carousel import CarouselGeneration
from src.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_admin_api_key)])


@router.get("/stats")
async def stats(
    session: AsyncSession = Depends(get_db_session),  # noqa: B008
) -> dict[str, int]:
    user_count = await session.scalar(select(func.count(User.id)))
    carousel_count = await session.scalar(select(func.count(CarouselGeneration.id)))
    return {
        "total_users": user_count or 0,
        "total_carousels": carousel_count or 0,
    }
