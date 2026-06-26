from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, EmailStr
from app.utility.model import BaseResponse, PyObjectId


class PasswordResetToken(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    user_id: PyObjectId
    token_hash: str  # Hashed token, never store raw token
    expires_at: datetime
    used: bool
    created_at: datetime
    used_at: Optional[datetime] = None

    @field_serializer("id")
    def serialize_id(self, v: ObjectId, _info):
        return str(v)

    @field_serializer("user_id")
    def serialize_user_id(self, v: ObjectId, _info):
        return str(v)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetValidateResponse(BaseModel):
    valid: bool
    message: Optional[str] = None


class PasswordResetCompleteRequest(BaseModel):
    token: str  # Raw token from email
    new_password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
