from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RolePrivilegeCreate(BaseModel):
    role_id: uuid.UUID
    privilege_code: str


class RolePrivilegeUpdate(BaseModel):
    role_id: uuid.UUID | None = None
    privilege_code: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class RolePrivilegeRead(BaseModel):
    id: uuid.UUID
    role_id: uuid.UUID
    privilege_code: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
