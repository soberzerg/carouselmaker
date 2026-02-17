from __future__ import annotations

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base


class Repository[T: Base]:
    def __init__(self, model: type[T], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: int) -> T | None:
        return await self.session.get(self.model, entity_id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        stmt = select(self.model).order_by(self.model.id).limit(limit).offset(offset)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: object) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: T, **kwargs: object) -> T:
        mapper = inspect(self.model)
        valid_columns = {c.key for c in mapper.column_attrs}
        for key, value in kwargs.items():
            if key not in valid_columns:
                raise ValueError(f"Invalid attribute '{key}' for {self.model.__name__}")
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        await self.session.delete(instance)
        await self.session.flush()
