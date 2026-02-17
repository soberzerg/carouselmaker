from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from src.models.credit import TransactionType


class CreditTransactionRead(BaseModel):
    id: int
    user_id: int
    amount: int
    transaction_type: TransactionType
    external_payment_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditPurchaseRequest(BaseModel):
    pack_index: int
