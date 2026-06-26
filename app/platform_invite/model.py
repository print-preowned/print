from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, EmailStr
from app.utility.model import BaseResponse, PyObjectId


class PlatformInvite(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    email: EmailStr
    platform_privilege_set_id: PyObjectId
    token_hash: str  # Hashed token, never store raw token (MDC-PU-S-4)
    expires_at: datetime
    status: str  # pending, accepted, rejected, expired
    invited_by: PyObjectId  # User ID of admin who created the invite
    created_at: datetime
    accepted_at: Optional[datetime] = None

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("platform_privilege_set_id")
    def serialize_platform_privilege_set_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("invited_by")
    def serialize_invited_by(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PlatformInviteCreateRequest(BaseModel):
    email: EmailStr
    platform_privilege_set_id: PyObjectId
    expires_in_days: int = 7  # Default 7 days expiration


class PlatformInviteValidateResponse(BaseModel):
    valid: bool
    invite: Optional[PlatformInvite] = None
    message: Optional[str] = None


class PlatformInviteAcceptRequest(BaseModel):
    token: str  # Raw token from email
    password: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None


class PlatformInviteRejectRequest(BaseModel):
    token: str  # Raw token from email
