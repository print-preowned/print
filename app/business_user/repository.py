from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_user.orm import BusinessUserOrm
from app.business_user.schemas import BusinessUserCreate, BusinessUserUpdate


class BusinessUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_business_user(self, payload: BusinessUserCreate) -> BusinessUserOrm:
        mapping = BusinessUserOrm(**payload.model_dump())
        self._session.add(mapping)
        await self._session.flush()
        return mapping

    async def update_business_user(
        self, business_user_id: uuid.UUID, payload: BusinessUserUpdate
    ) -> BusinessUserOrm | None:
        mapping = await self.read_business_user_by_id(business_user_id)
        if mapping is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(mapping, field, value)
        await self._session.flush()
        return mapping

    async def delete_business_user(self, business_user_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(BusinessUserOrm)
            .where(BusinessUserOrm.id == business_user_id, BusinessUserOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC))
            .returning(BusinessUserOrm.id)
        )
        return deleted_id is not None

    async def delete_by_business_id(self, business_id: uuid.UUID) -> int:
        result = await self._session.scalars(
            update(BusinessUserOrm)
            .where(
                BusinessUserOrm.business_id == business_id,
                BusinessUserOrm.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
            .returning(BusinessUserOrm.user_id)
        )
        return len(list(result))

    async def read_business_user_by_id(self, business_user_id: uuid.UUID) -> BusinessUserOrm | None:
        return await self._session.scalar(
            select(BusinessUserOrm).where(
                BusinessUserOrm.id == business_user_id, BusinessUserOrm.deleted_at.is_(None)
            )
        )

    async def read_business_user_by_user_id(self, user_id: uuid.UUID) -> BusinessUserOrm | None:
        return await self._session.scalar(
            select(BusinessUserOrm).where(
                BusinessUserOrm.user_id == user_id, BusinessUserOrm.deleted_at.is_(None)
            )
        )

    async def read_business_users_by_business_id(
        self, business_id: uuid.UUID
    ) -> list[BusinessUserOrm]:
        result = await self._session.scalars(
            select(BusinessUserOrm).where(
                BusinessUserOrm.business_id == business_id, BusinessUserOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def count_business_users(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(BusinessUserOrm)
            .where(BusinessUserOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_business_users(self, *, offset: int, limit: int) -> list[BusinessUserOrm]:
        statement: Select[tuple[BusinessUserOrm]] = (
            select(BusinessUserOrm)
            .where(BusinessUserOrm.deleted_at.is_(None))
            .order_by(BusinessUserOrm.created_at)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
