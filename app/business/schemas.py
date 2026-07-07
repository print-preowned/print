from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BusinessCreate(BaseModel):
    user_id: uuid.UUID
    name: str
    description: str | None = None
    logo: str | None = None


class BusinessUpdate(BaseModel):
    user_id: uuid.UUID | None = None
    name: str | None = None
    description: str | None = None
    logo: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BusinessRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    logo: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
