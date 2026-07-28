from __future__ import annotations

import math
from collections.abc import Callable
from typing import TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

from app.utility.model import PaginatedResponse, Pagination

T = TypeVar("T")

DEFAULT_PAGE = 1
DEFAULT_SIZE = 10
MAX_SIZE = 100


class PaginationParams(BaseModel):
    page: int = Field(default=DEFAULT_PAGE, ge=1)
    size: int = Field(default=DEFAULT_SIZE, ge=1, le=MAX_SIZE)
    search: str | None = None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size

    def normalized_search(self) -> str | None:
        if self.search is None:
            return None
        stripped = self.search.strip()
        return stripped or None


def pagination_params(
    page: int = Query(default=DEFAULT_PAGE, ge=1),
    size: int = Query(default=DEFAULT_SIZE, ge=1, le=MAX_SIZE),
    search: str | None = Query(default=None),
) -> PaginationParams:
    return PaginationParams(page=page, size=size, search=search)


def pagination_params_with(
    default_size: int = DEFAULT_SIZE,
) -> Callable[..., PaginationParams]:
    def _dependency(
        page: int = Query(default=DEFAULT_PAGE, ge=1),
        size: int = Query(default=default_size, ge=1, le=MAX_SIZE),
        search: str | None = Query(default=None),
    ) -> PaginationParams:
        return PaginationParams(page=page, size=size, search=search)

    return _dependency


def build_pagination_meta(params: PaginationParams, total_results: int) -> Pagination:
    total_pages = math.ceil(total_results / params.size) if params.size else 1
    return Pagination(
        page=params.page,
        size=params.size,
        total_pages=total_pages,
        total_results=total_results,
    )


def paginated_response(
    data: list[T],
    total_results: int,
    params: PaginationParams,
    *,
    message: str = "Successful",
    status_code: int = 200,
) -> PaginatedResponse[T]:
    return PaginatedResponse[T](
        status_code=status_code,
        message=message,
        data=data,
        pagination=build_pagination_meta(params, total_results),
    )
