from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductOptionCreate(BaseModel):
    name: str


class ProductOptionUpdate(BaseModel):
    name: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class ProductOptionRead(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
