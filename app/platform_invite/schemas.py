from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class PlatformInviteCreate(BaseModel):
    email: EmailStr
    platform_privilege_set_id: uuid.UUID


class PlatformInviteRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    platform_privilege_set_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    status: str
    invited_by: uuid.UUID
    created_at: datetime
    accepted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
