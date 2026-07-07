from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import BaseResponse, PyObjectId


class PlatformPrivilegeSetPrivilege(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    privilege_set_id: PyObjectId
    privilege_code: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("privilege_set_id")
    def serialize_privilege_set_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PlatformPrivilegeSetPrivilegeCreateRequest(BaseModel):
    privilege_set_id: str
    privilege_code: str
    status: str = "ACTIVE"


class PlatformPrivilegeSetPrivilegeUpdateRequest(BaseModel):
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
