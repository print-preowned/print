from datetime import datetime
from typing import Annotated, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_serializer, EmailStr
from app.user.schemas import UserRead
from app.utility.model import BaseResponse, PyObjectId


class User(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    role_id: Optional[PyObjectId] = None
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    country_code: Optional[str] = None
    phone_number: Optional[str] = None
    email: EmailStr
    profile_image: Optional[str] = None
    password: str
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
    role_id: Optional[PyObjectId] = None
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
