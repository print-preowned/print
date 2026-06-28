from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import BaseAppModel, BaseResponse, PyObjectId


class PlatformPrivilegeSet(BaseAppModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PlatformPrivilegeSetCreateRequest(BaseModel):
    name: str
    status: str = "ACTIVE"


class PlatformPrivilegeSetUpdateRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
