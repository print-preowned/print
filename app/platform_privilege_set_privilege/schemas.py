from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlatformPrivilegeSetPrivilegeCreate(BaseModel):
    privilege_set_id: uuid.UUID
    privilege_code: str


class PlatformPrivilegeSetPrivilegeUpdate(BaseModel):
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class PlatformPrivilegeSetPrivilegeRead(BaseModel):
    id: uuid.UUID
    privilege_set_id: uuid.UUID
    privilege_code: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
