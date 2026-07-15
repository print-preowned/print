from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderCreate(BaseModel):
    user_id: uuid.UUID
    reference: str
    currency: str = "NGN"
    total_amount: Decimal


class OrderUpdate(BaseModel):
    user_id: uuid.UUID | None = None
    reference: str | None = None
    currency: str | None = None
    total_amount: Decimal | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class OrderRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    reference: str
    currency: str
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
