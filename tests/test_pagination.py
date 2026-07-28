from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.utility.pagination import (
    PaginationParams,
    build_pagination_meta,
    paginated_response,
)


def test_default_params() -> None:
    params = PaginationParams()
    assert params.page == 1
    assert params.size == 10
    assert params.offset == 0
    assert params.limit == 10
    assert params.search is None


def test_offset_for_page_three() -> None:
    params = PaginationParams(page=3, size=20)
    assert params.offset == 40


@pytest.mark.parametrize(
    ("page", "size"),
    [
        (0, 10),
        (-1, 10),
        (1, 0),
        (1, -5),
        (1, 101),
    ],
)
def test_invalid_page_or_size_rejected(page: int, size: int) -> None:
    with pytest.raises(ValidationError):
        PaginationParams(page=page, size=size)


def test_empty_result_set_total_pages() -> None:
    params = PaginationParams(page=1, size=10)
    meta = build_pagination_meta(params, total_results=0)
    assert meta.total_pages == 0
    assert meta.total_results == 0


def test_last_partial_page_total_pages() -> None:
    params = PaginationParams(page=1, size=10)
    meta = build_pagination_meta(params, total_results=47)
    assert meta.total_pages == 5


@pytest.mark.parametrize(
    ("search", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("  hello  ", "hello"),
        ("query", "query"),
    ],
)
def test_normalized_search(search: str | None, expected: str | None) -> None:
    params = PaginationParams(search=search)
    assert params.normalized_search() == expected


def test_paginated_response_envelope() -> None:
    params = PaginationParams(page=2, size=5)
    response = paginated_response(["a", "b"], total_results=12, params=params)

    assert response.status_code == 200
    assert response.message == "Successful"
    assert response.data == ["a", "b"]
    assert response.pagination is not None
    assert response.pagination.page == 2
    assert response.pagination.size == 5
    assert response.pagination.total_results == 12
    assert response.pagination.total_pages == 3
