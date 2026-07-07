from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from app.utility.model import BaseAppModel, BaseResponse, PyObjectId


class PlatformInvite(BaseAppModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    email: EmailStr
    platform_privilege_set_id: PyObjectId
    token_hash: str  # Hashed token, never store raw token (MDC-PU-S-4)
    expires_at: datetime
    status: str  # pending, accepted, rejected, expired
    invited_by: PyObjectId  # User ID of admin who created the invite
    created_at: datetime
    accepted_at: Optional[datetime] = None


class PlatformInviteCreateRequest(BaseModel):
    email: EmailStr
    platform_privilege_set_id: str


class PlatformInviteResendRequest(BaseModel):
    platform_privilege_set_id: str | None = None


class PlatformInviteActionResponse(BaseModel):
    invite_id: str
    expires_at: str
    message: str


class PlatformInviteSummary(BaseModel):
    id: str
    email: EmailStr
    platform_privilege_set_id: str
    expires_at: datetime
    status: str
    invited_by: str
    created_at: datetime
    accepted_at: Optional[datetime] = None


class PlatformInviteValidateResponse(BaseModel):
    valid: bool
    invite: Optional[PlatformInviteSummary] = None
    message: Optional[str] = None


class PlatformInviteAcceptRequest(BaseModel):
    token: str  # Raw token from email
    password: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None


class PlatformInviteRejectRequest(BaseModel):
    token: str  # Raw token from email


class PlatformInviteWithPrivilegeSet(PlatformInvite):
    """Platform invite with populated privilege set name for list/read."""
    platform_privilege_set_name: Optional[str] = None
