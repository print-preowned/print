from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BusinessAddressCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=32)
    phone_number: Optional[str] = Field(default=None, max_length=16)
    line1: str = Field(min_length=1, max_length=128)
    line2: Optional[str] = Field(default=None, max_length=128)
    city: str = Field(min_length=1, max_length=32)
    state: str = Field(min_length=1, max_length=32)
    postal_code: Optional[str] = Field(default=None, max_length=8)
    country_code: str = Field(default="NG", min_length=2, max_length=3)
    is_primary: bool = False
    pickup_enabled: bool = False


class BusinessAddressUpdateRequest(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=32)
    phone_number: Optional[str] = Field(default=None, max_length=16)
    line1: Optional[str] = Field(default=None, min_length=1, max_length=128)
    line2: Optional[str] = Field(default=None, max_length=128)
    city: Optional[str] = Field(default=None, min_length=1, max_length=32)
    state: Optional[str] = Field(default=None, min_length=1, max_length=32)
    postal_code: Optional[str] = Field(default=None, max_length=8)
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=3)
    is_primary: Optional[bool] = None
    pickup_enabled: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")
