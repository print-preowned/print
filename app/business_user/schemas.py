from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BusinessUserCreate(BaseModel):
    business_id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID


class BusinessUserUpdate(BaseModel):
    business_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class BusinessUserRead(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
