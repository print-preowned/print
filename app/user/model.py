from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.user.schemas import UserRead
from app.utility.model import BaseResponse


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    status: str = "NEW"


class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    country_code: Optional[str] = None
    phone_number: Optional[str] = None
    email: EmailStr
    profile_image: Optional[str] = None
    password: str
    status: str = "ACTIVE"


class UserUpdateRequest(BaseModel):
    role_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    country_code: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_image: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class LoginResponse(BaseResponse[UserRead]):
    token: str


class ContextSwitchRequest(BaseModel):
    target_context: str  # "CUSTOMER" or "BUSINESS"


class ContextSwitchResponse(BaseModel):
    status_code: int
    message: str
    token: str
