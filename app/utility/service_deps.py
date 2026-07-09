"""FastAPI DI helpers for request-scoped service classes."""

from __future__ import annotations

from typing import Annotated, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.postgres import get_db, get_session

T = TypeVar("T")


def writable_service(base: type[T]) -> type[T]:
    """Subclass *base* so FastAPI injects a committing session via ``get_db``."""

    class _Writable(base):  # type: ignore[misc, valid-type]
        def __init__(self, session: Annotated[AsyncSession, Depends(get_db)]) -> None:
            super().__init__(session)

    _Writable.__name__ = f"Writable{base.__name__}"
    _Writable.__qualname__ = f"Writable{base.__name__}"
    return _Writable  # type: ignore[return-value]


def readable_service(base: type[T]) -> type[T]:
    """Subclass *base* so FastAPI injects a read-only session via ``get_session``."""

    class _Readable(base):  # type: ignore[misc, valid-type]
        def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]) -> None:
            super().__init__(session)

    _Readable.__name__ = f"Readable{base.__name__}"
    _Readable.__qualname__ = f"Readable{base.__name__}"
    return _Readable  # type: ignore[return-value]
