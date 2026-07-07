from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.utility.model import PyObjectId


class RolePrivilege(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    role_id: PyObjectId
    privilege_code: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("role_id")
    def serialize_role_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RolePrivilegeCreateRequest(BaseModel):
    role_id: str
    privilege_code: str


class RolePrivilegeUpdateRequest(BaseModel):
    role_id: str | None = None
    privilege_code: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


