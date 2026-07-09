from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_rating.orm import BusinessRatingOrm
from app.business_rating.schemas import BusinessRatingCreate, BusinessRatingUpdate


class BusinessRatingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_business_rating(self, payload: BusinessRatingCreate) -> BusinessRatingOrm:
        row = BusinessRatingOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_business_rating(
        self, rating_id: uuid.UUID, payload: BusinessRatingUpdate
    ) -> BusinessRatingOrm | None:
        row = await self.read_business_rating_by_id(rating_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def soft_delete_business_rating(self, rating_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BusinessRatingOrm)
            .where(BusinessRatingOrm.id == rating_id, BusinessRatingOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(BusinessRatingOrm.id)
        )
        return deleted_id is not None

    async def read_business_rating_by_id(self, rating_id: uuid.UUID) -> BusinessRatingOrm | None:
        return await self._session.scalar(
            select(BusinessRatingOrm).where(
                BusinessRatingOrm.id == rating_id, BusinessRatingOrm.deleted_at.is_(None)
            )
        )

    async def read_by_business_id(self, business_id: uuid.UUID) -> list[BusinessRatingOrm]:
        result = await self._session.scalars(
            select(BusinessRatingOrm).where(
                BusinessRatingOrm.business_id == business_id, BusinessRatingOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def count_business_ratings(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(BusinessRatingOrm)
            .where(BusinessRatingOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_business_ratings(self, *, offset: int, limit: int) -> list[BusinessRatingOrm]:
        statement: Select[tuple[BusinessRatingOrm]] = (
            select(BusinessRatingOrm)
            .where(BusinessRatingOrm.deleted_at.is_(None))
            .order_by(BusinessRatingOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
