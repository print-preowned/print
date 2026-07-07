from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlatformUserCreate(BaseModel):
    user_id: uuid.UUID
    platform_privilege_set_id: uuid.UUID


class PlatformUserUpdate(BaseModel):
    platform_privilege_set_id: uuid.UUID | None = None
    status: str | None = None

    model_config = ConfigDict(extra="forbid")


class PlatformUserRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    platform_privilege_set_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
