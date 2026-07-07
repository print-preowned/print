from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BusinessBookCreate(BaseModel):
    book_id: uuid.UUID
    business_id: uuid.UUID
    synopsis: str | None = None
    image: str | None = None
    status: str = "DRAFT"


class BusinessBookUpdate(BaseModel):
    book_id: uuid.UUID | None = None
    synopsis: str | None = None
    image: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BusinessBookRead(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID
    business_id: uuid.UUID
    synopsis: str | None
    image: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
