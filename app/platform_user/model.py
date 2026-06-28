from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, EmailStr
from app.user.model import SignupRequest
from app.utility.model import BaseAppModel, BaseResponse, PyObjectId


class PlatformUser(BaseAppModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    user_id: PyObjectId
    platform_privilege_set_id: PyObjectId
    status: str
    created_at: datetime
    updated_at: datetime

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


class SuperAdminTransferRequest(BaseModel):
    target_platform_user_id: PyObjectId

    model_config = ConfigDict(extra="forbid")


class PlatformUserWithUser(PlatformUser):
    """Platform user with populated user email and name for list/read."""
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    platform_privilege_set_name: Optional[str] = None
    is_super_admin: Optional[bool] = None
