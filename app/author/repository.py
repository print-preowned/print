from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.author.orm import AuthorOrm
from app.author.schemas import AuthorCreate, AuthorUpdate


class AuthorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_author(self, payload: AuthorCreate) -> AuthorOrm:
        author = AuthorOrm(**payload.model_dump())
        self._session.add(author)
        await self._session.flush()
        return author

    async def update_author(self, author_id: uuid.UUID, payload: AuthorUpdate) -> AuthorOrm | None:
        author = await self.read_author_by_id(author_id)
        if author is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(author, field, value)
        await self._session.flush()
        return author

    async def soft_delete_author(self, author_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(AuthorOrm)
            .where(AuthorOrm.id == author_id, AuthorOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(AuthorOrm.id)
        )
        return deleted_id is not None

    async def read_author_by_id(self, author_id: uuid.UUID) -> AuthorOrm | None:
        return await self._session.scalar(
            select(AuthorOrm).where(AuthorOrm.id == author_id, AuthorOrm.deleted_at.is_(None))
        )

    async def read_authors_by_ids(self, author_ids: list[uuid.UUID]) -> list[AuthorOrm]:
        if not author_ids:
            return []
        result = await self._session.scalars(
            select(AuthorOrm).where(AuthorOrm.id.in_(author_ids), AuthorOrm.deleted_at.is_(None))
        )
        return list(result)

    async def count_authors(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(AuthorOrm).where(AuthorOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_authors(self, *, offset: int, limit: int) -> list[AuthorOrm]:
        statement: Select[tuple[AuthorOrm]] = (
            select(AuthorOrm)
            .where(AuthorOrm.deleted_at.is_(None))
            .order_by(AuthorOrm.last_name, AuthorOrm.first_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
