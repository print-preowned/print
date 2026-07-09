from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_book.orm import BusinessBookOrm
from app.business_book.schemas import BusinessBookCreate, BusinessBookUpdate


class BusinessBookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_business_book(self, payload: BusinessBookCreate) -> BusinessBookOrm:
        row = BusinessBookOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_business_book(
        self, business_book_id: uuid.UUID, payload: BusinessBookUpdate
    ) -> BusinessBookOrm | None:
        row = await self.read_business_book_by_id(business_book_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def soft_delete_business_book(self, business_book_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BusinessBookOrm)
            .where(BusinessBookOrm.id == business_book_id, BusinessBookOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(BusinessBookOrm.id)
        )
        return deleted_id is not None

    async def read_business_book_by_id(self, business_book_id: uuid.UUID) -> BusinessBookOrm | None:
        return await self._session.scalar(
            select(BusinessBookOrm).where(
                BusinessBookOrm.id == business_book_id,
                BusinessBookOrm.deleted_at.is_(None),
                BusinessBookOrm.status != "DELETED",
            )
        )

    async def read_business_books_by_ids(
        self, business_book_ids: list[uuid.UUID]
    ) -> list[BusinessBookOrm]:
        if not business_book_ids:
            return []
        result = await self._session.scalars(
            select(BusinessBookOrm).where(
                BusinessBookOrm.id.in_(business_book_ids),
                BusinessBookOrm.deleted_at.is_(None),
                BusinessBookOrm.status != "DELETED",
            )
        )
        return list(result)

    async def count_business_books(self, *, business_id: uuid.UUID | None = None) -> int:
        statement = (
            select(func.count())
            .select_from(BusinessBookOrm)
            .where(BusinessBookOrm.deleted_at.is_(None), BusinessBookOrm.status != "DELETED")
        )
        if business_id is not None:
            statement = statement.where(BusinessBookOrm.business_id == business_id)
        total = await self._session.scalar(statement)
        return int(total or 0)

    async def list_business_books(
        self, *, offset: int, limit: int, business_id: uuid.UUID | None = None
    ) -> list[BusinessBookOrm]:
        statement: Select[tuple[BusinessBookOrm]] = (
            select(BusinessBookOrm)
            .where(BusinessBookOrm.deleted_at.is_(None), BusinessBookOrm.status != "DELETED")
            .order_by(BusinessBookOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if business_id is not None:
            statement = statement.where(BusinessBookOrm.business_id == business_id)
        result = await self._session.scalars(statement)
        return list(result)
