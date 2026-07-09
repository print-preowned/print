from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.orm import BusinessOrm
from app.business.schemas import BusinessCreate, BusinessUpdate


class BusinessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payload: BusinessCreate) -> BusinessOrm:
        business = BusinessOrm(**payload.model_dump())
        self._session.add(business)
        await self._session.flush()
        return business

    async def update(
        self,
        business_id: uuid.UUID,
        payload: BusinessUpdate,
    ) -> BusinessOrm | None:
        business = await self.read_by_id(business_id)
        if business is None:
            return None

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(business, field, value)
        await self._session.flush()
        return business

    async def delete(self, business_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BusinessOrm)
            .where(BusinessOrm.id == business_id, BusinessOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC))
            .returning(BusinessOrm.id)
        )
        return deleted_id is not None

    async def read_by_id(self, business_id: uuid.UUID) -> BusinessOrm | None:
        return await self._session.scalar(
            select(BusinessOrm).where(
                BusinessOrm.id == business_id,
                BusinessOrm.deleted_at.is_(None),
            )
        )

    async def read_by_user_id(self, user_id: uuid.UUID) -> BusinessOrm | None:
        return await self._session.scalar(
            select(BusinessOrm).where(
                BusinessOrm.user_id == user_id,
                BusinessOrm.deleted_at.is_(None),
            )
        )

    async def count(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(BusinessOrm).where(BusinessOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list(self, *, offset: int, limit: int) -> list[BusinessOrm]:
        statement: Select[tuple[BusinessOrm]] = (
            select(BusinessOrm)
            .where(BusinessOrm.deleted_at.is_(None))
            .order_by(BusinessOrm.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
