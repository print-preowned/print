from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PrivilegeCreate(BaseModel):
    code: str
    name: str
    module_name: str


class PrivilegeUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    module_name: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class PrivilegeRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    module_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
