from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

# Role code constants
OWNER_ROLE_CODE = "OWNER"


class Role(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class RoleCreateRequest(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    status: str = "ACTIVE"


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
