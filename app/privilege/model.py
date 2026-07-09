from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Privilege(BaseModel):
    id: str
    code: str
    name: str
    module_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class PrivilegeCreateRequest(BaseModel):
    code: str
    name: str
    module_name: str
    status: str = "ACTIVE"


class PrivilegeUpdateRequest(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    module_name: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
