from re import search
from typing import Generic, List, Optional, Any, TypeVar
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import (
    BaseModel,
    ConfigDict,
    GetCoreSchemaHandler,
    field_serializer,
    field_validator,
)
from pydantic_core import core_schema

T = TypeVar("T")

class BaseAppModel(BaseModel):
    """Base for MongoDB-backed entity models."""

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @field_validator("*", mode="before")
    @classmethod
    def ensure_utc(cls, v: Any) -> Any:
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_serializer("*")
    def serialize_object_ids(self, v: Any) -> Any:
        if isinstance(v, ObjectId):
            return str(v)
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



class BaseFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = None
    created_from: Optional[str] = None
    created_to: Optional[str] = None


class ParamRequest(BaseModel, Generic[T]):
    page: int
    size: int
    search: Optional[str] = None
    filter: Optional[T | BaseFilter] = None


class Pagination(BaseModel):
    page: int
    size: int
    total_pages: int
    total_results: int


class BaseResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: T

    model_config = ConfigDict(
        extra="allow",
        json_encoders={ObjectId: str}
    )


class PaginatedResponse(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: List[T]
    pagination: Pagination | None


class PaginatedData(BaseModel, Generic[T]):
    data: List[T]
    pagination: Pagination | None

class PyObjectId(ObjectId):
    """Custom type for Pydantic v2 that accepts and outputs ObjectId as str."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.str_schema(),
                ]
            ),
        )

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            return ObjectId(v)
        raise TypeError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, _handler
    ) -> dict[str, Any]:
        return {"type": "string"}

