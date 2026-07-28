from datetime import datetime, timezone
from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


class BaseAppModel(BaseModel):
    """Base for API entity models."""

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("*", mode="before")
    @classmethod
    def ensure_utc(cls, v: Any) -> Any:
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    def __getitem__(self, key: str) -> Any:
        """Dynamically fetches any instance field by its string name."""
        try:
            return self.__dict__[key]
        except KeyError:
            raise KeyError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __iter__(self) -> Any:
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)


class Pagination(BaseModel):
    page: int
    size: int
    total_pages: int
    total_results: int


class BaseResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: T

    model_config = ConfigDict(extra="allow")


class PaginatedResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: List[T]
    pagination: Pagination | None
