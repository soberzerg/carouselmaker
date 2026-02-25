from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from src.models.base import Base


@pytest.fixture(scope="session")
def postgres_url():
    """Spin up a real PostgreSQL container for the test session."""
    with PostgresContainer("postgres:16-alpine") as pg:
        # testcontainers returns a psycopg2 URL; convert to asyncpg
        sync_url = pg.get_connection_url()
        async_url = sync_url.replace("psycopg2", "asyncpg")
        yield async_url


@pytest.fixture
async def engine(postgres_url):
    engine = create_async_engine(postgres_url, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
