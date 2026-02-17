from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.db.session import get_async_session

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async for session in get_async_session():
        yield session


async def verify_admin_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    settings = get_settings()
    expected = settings.admin_api_key.get_secret_value()
    if not api_key or api_key != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


DBSession = Depends(get_db_session)
