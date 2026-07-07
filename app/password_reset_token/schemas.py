from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PasswordResetTokenCreate(BaseModel):
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime


class PasswordResetTokenRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    used: bool
    created_at: datetime
    used_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
