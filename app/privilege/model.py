from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class Privilege(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    code: str
    name: str
    module_name: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


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


