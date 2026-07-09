from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.utility.model import BaseAppModel


class PlatformPrivilegeSet(BaseAppModel):
    id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


class PlatformPrivilegeSetCreateRequest(BaseModel):
    name: str
    status: str = "ACTIVE"


class PlatformPrivilegeSetUpdateRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
