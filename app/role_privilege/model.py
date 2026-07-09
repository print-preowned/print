from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RolePrivilege(BaseModel):
    id: str
    role_id: str
    privilege_code: str
    status: str
    created_at: datetime
    updated_at: datetime


class RolePrivilegeCreateRequest(BaseModel):
    role_id: str
    privilege_code: str


class RolePrivilegeUpdateRequest(BaseModel):
    role_id: str | None = None
    privilege_code: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
