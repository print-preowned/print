from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book.orm import BookOrm
from app.business_book.orm import BusinessBookOrm
from app.business_book.schemas import BusinessBookCreate, BusinessBookUpdate
from app.variant.orm import VariantOrm


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

    def _public_catalog_base(
        self,
        *,
        book_id: uuid.UUID | None = None,
        exclude_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> Select[tuple[BusinessBookOrm]]:
        statement: Select[tuple[BusinessBookOrm]] = (
            select(BusinessBookOrm)
            .join(VariantOrm, VariantOrm.business_book_id == BusinessBookOrm.id)
            .where(
                BusinessBookOrm.deleted_at.is_(None),
                BusinessBookOrm.status == "ACTIVE",
                VariantOrm.deleted_at.is_(None),
                VariantOrm.status == "ACTIVE",
                VariantOrm.stock > 0,
            )
        )
        if book_id is not None:
            statement = statement.where(BusinessBookOrm.book_id == book_id)
        if exclude_id is not None:
            statement = statement.where(BusinessBookOrm.id != exclude_id)
        if search:
            statement = statement.join(BookOrm, BookOrm.id == BusinessBookOrm.book_id).where(
                BookOrm.title.ilike(f"%{search}%"),
                BookOrm.deleted_at.is_(None),
            )
        return statement

    async def count_public_catalog(
        self,
        *,
        book_id: uuid.UUID | None = None,
        exclude_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> int:
        statement = select(func.count(func.distinct(BusinessBookOrm.id))).select_from(
            BusinessBookOrm
        ).join(
            VariantOrm, VariantOrm.business_book_id == BusinessBookOrm.id
        ).where(
            BusinessBookOrm.deleted_at.is_(None),
            BusinessBookOrm.status == "ACTIVE",
            VariantOrm.deleted_at.is_(None),
            VariantOrm.status == "ACTIVE",
            VariantOrm.stock > 0,
        )
        if book_id is not None:
            statement = statement.where(BusinessBookOrm.book_id == book_id)
        if exclude_id is not None:
            statement = statement.where(BusinessBookOrm.id != exclude_id)
        if search:
            statement = statement.join(BookOrm, BookOrm.id == BusinessBookOrm.book_id).where(
                BookOrm.title.ilike(f"%{search}%"),
                BookOrm.deleted_at.is_(None),
            )
        total = await self._session.scalar(statement)
        return int(total or 0)

    async def list_public_catalog(
        self,
        *,
        offset: int,
        limit: int,
        book_id: uuid.UUID | None = None,
        exclude_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> list[BusinessBookOrm]:
        statement = (
            self._public_catalog_base(
                book_id=book_id, exclude_id=exclude_id, search=search
            )
            .group_by(BusinessBookOrm.id)
            .order_by(BusinessBookOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
