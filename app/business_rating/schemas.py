from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BusinessRatingCreate(BaseModel):
    business_id: uuid.UUID
    user_id: uuid.UUID
    order_item_id: uuid.UUID | None = None
    rating: int = Field(ge=1, le=5)
    review: str | None = None


class BusinessRatingUpdate(BaseModel):
    business_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    order_item_id: uuid.UUID | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    review: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BusinessRatingRead(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    user_id: uuid.UUID
    order_item_id: uuid.UUID | None
    rating: int
    review: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
