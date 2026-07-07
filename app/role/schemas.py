from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoleCreate(BaseModel):
    name: str
    code: str
    description: str | None = None


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class RoleRead(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
