from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.user_address.orm import UserAddressOrm
from app.user_address.schemas import UserAddressCreate, UserAddressUpdate


class UserAddressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payload: UserAddressCreate) -> UserAddressOrm:
        row = UserAddressOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def read_by_id(self, address_id: uuid.UUID, user_id: uuid.UUID) -> UserAddressOrm | None:
        return await self._session.scalar(
            select(UserAddressOrm).where(
                UserAddressOrm.id == address_id,
                UserAddressOrm.user_id == user_id,
                UserAddressOrm.deleted_at.is_(None),
            )
        )

    async def update(
        self,
        address_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: UserAddressUpdate,
    ) -> UserAddressOrm | None:
        row = await self.read_by_id(address_id, user_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def delete(self, address_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(UserAddressOrm)
            .where(
                UserAddressOrm.id == address_id,
                UserAddressOrm.user_id == user_id,
                UserAddressOrm.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
            .returning(UserAddressOrm.id)
        )
        return deleted_id is not None

    async def count_active_by_user(self, user_id: uuid.UUID) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(UserAddressOrm)
            .where(UserAddressOrm.user_id == user_id, UserAddressOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int,
        limit: int,
    ) -> list[UserAddressOrm]:
        result = await self._session.scalars(
            select(UserAddressOrm)
            .where(UserAddressOrm.user_id == user_id, UserAddressOrm.deleted_at.is_(None))
            .order_by(UserAddressOrm.is_default.desc(), UserAddressOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result)

    async def clear_default_for_user(self, user_id: uuid.UUID, *, exclude_id: uuid.UUID | None = None) -> None:
        statement = (
            update(UserAddressOrm)
            .where(
                UserAddressOrm.user_id == user_id,
                UserAddressOrm.deleted_at.is_(None),
                UserAddressOrm.is_default.is_(True),
            )
            .values(is_default=False)
        )
        if exclude_id is not None:
            statement = statement.where(UserAddressOrm.id != exclude_id)
        await self._session.execute(statement)

    async def find_first_active_for_user(
        self,
        user_id: uuid.UUID,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> UserAddressOrm | None:
        statement = (
            select(UserAddressOrm)
            .where(UserAddressOrm.user_id == user_id, UserAddressOrm.deleted_at.is_(None))
            .order_by(UserAddressOrm.created_at.asc())
            .limit(1)
        )
        if exclude_id is not None:
            statement = statement.where(UserAddressOrm.id != exclude_id)
        return await self._session.scalar(statement)

    async def set_default(self, address_id: uuid.UUID, user_id: uuid.UUID) -> UserAddressOrm | None:
        row = await self.read_by_id(address_id, user_id)
        if row is None:
            return None
        await self.clear_default_for_user(user_id, exclude_id=address_id)
        row.is_default = True
        await self._session.flush()
        return row
