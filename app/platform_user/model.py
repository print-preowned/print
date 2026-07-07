from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from app.user.model import SignupRequest
from app.utility.model import BaseAppModel, BaseResponse, PyObjectId


class PlatformUser(BaseAppModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    user_id: str
    platform_privilege_set_id: PyObjectId
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("user_id", mode="before")
    @classmethod
    def normalize_user_id(cls, value: object) -> str:
        from bson import ObjectId

        if isinstance(value, ObjectId):
            return str(value)
        return str(value)

class PlatformUserSignupRequest(SignupRequest):
    platform_privilege_set_id: str


class PlatformUserCreateRequest(BaseModel):
    user_id: str
    platform_privilege_set_id: str
    status: str = "ACTIVE"


class PlatformUserUpdateRequest(BaseModel):
    platform_privilege_set_id: Optional[str] = None
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
