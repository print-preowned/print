from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class Business(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("user_id", mode="before")
    @classmethod
    def normalize_user_id(cls, value: object) -> str:
        return str(value)




class BusinessCreateRequest(BaseModel):
    user_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    status: str = "ACTIVE"


class BusinessUpdateRequest(BaseModel):
    user_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class BusinessCreateResponse(BaseModel):
    token: str


