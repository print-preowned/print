from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_address.orm import BusinessAddressOrm
from app.business_address.schemas import BusinessAddressCreate, BusinessAddressUpdate


class BusinessAddressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payload: BusinessAddressCreate) -> BusinessAddressOrm:
        row = BusinessAddressOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def read_by_id(
        self,
        address_id: uuid.UUID,
        business_id: uuid.UUID,
    ) -> BusinessAddressOrm | None:
        return await self._session.scalar(
            select(BusinessAddressOrm).where(
                BusinessAddressOrm.id == address_id,
                BusinessAddressOrm.business_id == business_id,
                BusinessAddressOrm.deleted_at.is_(None),
            )
        )

    async def update(
        self,
        address_id: uuid.UUID,
        business_id: uuid.UUID,
        payload: BusinessAddressUpdate,
    ) -> BusinessAddressOrm | None:
        row = await self.read_by_id(address_id, business_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def delete(self, address_id: uuid.UUID, business_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BusinessAddressOrm)
            .where(
                BusinessAddressOrm.id == address_id,
                BusinessAddressOrm.business_id == business_id,
                BusinessAddressOrm.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
            .returning(BusinessAddressOrm.id)
        )
        return deleted_id is not None

    async def count_active_by_business(self, business_id: uuid.UUID) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(BusinessAddressOrm)
            .where(
                BusinessAddressOrm.business_id == business_id,
                BusinessAddressOrm.deleted_at.is_(None),
            )
        )
        return int(total or 0)

    async def list_by_business(
        self,
        business_id: uuid.UUID,
        *,
        offset: int,
        limit: int,
    ) -> list[BusinessAddressOrm]:
        result = await self._session.scalars(
            select(BusinessAddressOrm)
            .where(
                BusinessAddressOrm.business_id == business_id,
                BusinessAddressOrm.deleted_at.is_(None),
            )
            .order_by(BusinessAddressOrm.is_primary.desc(), BusinessAddressOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result)

    async def clear_primary_for_business(
        self,
        business_id: uuid.UUID,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        statement = (
            update(BusinessAddressOrm)
            .where(
                BusinessAddressOrm.business_id == business_id,
                BusinessAddressOrm.deleted_at.is_(None),
                BusinessAddressOrm.is_primary.is_(True),
            )
            .values(is_primary=False)
        )
        if exclude_id is not None:
            statement = statement.where(BusinessAddressOrm.id != exclude_id)
        await self._session.execute(statement)

    async def find_first_active_for_business(
        self,
        business_id: uuid.UUID,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> BusinessAddressOrm | None:
        statement = (
            select(BusinessAddressOrm)
            .where(
                BusinessAddressOrm.business_id == business_id,
                BusinessAddressOrm.deleted_at.is_(None),
            )
            .order_by(BusinessAddressOrm.created_at.asc())
            .limit(1)
        )
        if exclude_id is not None:
            statement = statement.where(BusinessAddressOrm.id != exclude_id)
        return await self._session.scalar(statement)

    async def set_primary(
        self,
        address_id: uuid.UUID,
        business_id: uuid.UUID,
    ) -> BusinessAddressOrm | None:
        row = await self.read_by_id(address_id, business_id)
        if row is None:
            return None
        await self.clear_primary_for_business(business_id, exclude_id=address_id)
        row.is_primary = True
        await self._session.flush()
        return row

    async def clear_pickup_enabled_for_business(
        self,
        business_id: uuid.UUID,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        statement = (
            update(BusinessAddressOrm)
            .where(
                BusinessAddressOrm.business_id == business_id,
                BusinessAddressOrm.deleted_at.is_(None),
                BusinessAddressOrm.pickup_enabled.is_(True),
            )
            .values(pickup_enabled=False)
        )
        if exclude_id is not None:
            statement = statement.where(BusinessAddressOrm.id != exclude_id)
        await self._session.execute(statement)

    async def read_pickup_location_by_business(
        self,
        business_id: uuid.UUID,
    ) -> BusinessAddressOrm | None:
        return await self._session.scalar(
            select(BusinessAddressOrm).where(
                BusinessAddressOrm.business_id == business_id,
                BusinessAddressOrm.deleted_at.is_(None),
                BusinessAddressOrm.pickup_enabled.is_(True),
            )
        )
