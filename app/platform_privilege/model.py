from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import BaseResponse


class PlatformPrivilege(BaseModel):
    id: str
    code: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime




class PlatformPrivilegeCreateRequest(BaseModel):
    code: str
    description: Optional[str] = None
    status: str = "ACTIVE"


class PlatformPrivilegeUpdateRequest(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
