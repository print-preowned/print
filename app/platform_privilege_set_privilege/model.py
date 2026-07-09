from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlatformPrivilegeSetPrivilege(BaseModel):
    id: str
    privilege_set_id: str
    privilege_code: str
    status: str
    created_at: datetime
    updated_at: datetime


class PlatformPrivilegeSetPrivilegeCreateRequest(BaseModel):
    privilege_set_id: str
    privilege_code: str
    status: str = "ACTIVE"


class PlatformPrivilegeSetPrivilegeUpdateRequest(BaseModel):
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
