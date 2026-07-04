from __future__ import annotations

import uuid

from app.genre.schemas import GenreRead
from app.utility.postgres import get_sessionmaker

from . import repository


async def read_by_ids_query(ids: list[str]) -> list[GenreRead]:
    """Batch-read genres by id for cross-domain callers still on the query module."""
    genre_ids: list[uuid.UUID] = []
    for genre_id in ids:
        try:
            genre_ids.append(uuid.UUID(genre_id))
        except ValueError:
            continue

    if not genre_ids:
        return []

    async with get_sessionmaker()() as session:
        rows = await repository.read_genres_by_ids(session, genre_ids)
    return [GenreRead.model_validate(row) for row in rows]
