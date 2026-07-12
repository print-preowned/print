from datetime import datetime

from pydantic import BaseModel


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
