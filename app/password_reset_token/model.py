from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class PasswordResetToken(BaseModel):
    id: str
    user_id: str
    token_hash: str  # Hashed token, never store raw token
    expires_at: datetime
    used: bool
    created_at: datetime
    used_at: Optional[datetime] = None


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


class PasswordChangeResponse(BaseModel):
    message: str = "Password changed successfully"
    token: Optional[str] = None
