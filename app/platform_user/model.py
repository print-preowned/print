from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, EmailStr
from app.user.model import SignupRequest
from app.utility.model import BaseResponse, PyObjectId


class PlatformUser(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    user_id: PyObjectId
    platform_privilege_set_id: PyObjectId
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("user_id")
    def serialize_user_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("platform_privilege_set_id")
    def serialize_platform_privilege_set_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)

class PlatformUserSignupRequest(SignupRequest):
    platform_privilege_set_id: PyObjectId


class PlatformUserCreateRequest(BaseModel):
    user_id: PyObjectId
    platform_privilege_set_id: PyObjectId
    status: str = "ACTIVE"


class PlatformUserUpdateRequest(BaseModel):
    platform_privilege_set_id: Optional[PyObjectId] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class PlatformUserWithUser(PlatformUser):
    """Platform user with populated user email and name for list/read."""
    user_email: Optional[str] = None
    user_name: Optional[str] = None
