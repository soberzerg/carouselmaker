from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserBase(BaseModel):
    telegram_id: int
    username: str | None = None
    full_name: str | None = None


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int
    credit_balance: int
    created_at: datetime

    model_config = {"from_attributes": True}
