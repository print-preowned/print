from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class BusinessUser(BaseModel):
    id: str
    business_id: str
    user_id: str
    role_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("user_id", "role_id", mode="before")
    @classmethod
    def normalize_user_refs(cls, value: object) -> str:
        return str(value)


class BusinessUserCreateRequest(BaseModel):
    business_id: str
    user_id: str
    role_id: str
    status: str = "ACTIVE"


class BusinessUserUpdateRequest(BaseModel):
    business_id: Optional[str] = None
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
