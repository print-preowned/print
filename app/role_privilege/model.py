from datetime import datetime

from pydantic import BaseModel, Field


class RolePrivilege(BaseModel):
    id: str
    role_id: str
    privilege_code: str
    status: str
    created_at: datetime
    updated_at: datetime



class RolePrivilegeCreateRequest(BaseModel):
    privilege_codes: list[str] = Field(default_factory=list)
