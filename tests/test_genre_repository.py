"""Genre repository unit tests (no database required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.genre.repository import soft_delete_genre


@pytest.mark.asyncio
async def test_soft_delete_genre_returns_true_when_row_updated() -> None:
    genre_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=genre_id)

    deleted = await soft_delete_genre(session, genre_id)

    assert deleted is True
    session.scalar.assert_awaited_once()


@pytest.mark.asyncio
async def test_soft_delete_genre_returns_false_when_missing() -> None:
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    deleted = await soft_delete_genre(session, uuid.uuid4())

    assert deleted is False
