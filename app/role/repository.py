from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.role.orm import RoleOrm
from app.role.schemas import RoleCreate, RoleUpdate


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_role(self, payload: RoleCreate) -> RoleOrm:
        role = RoleOrm(**payload.model_dump())
        self._session.add(role)
        await self._session.flush()
        return role

    async def update_role(self, role_id: uuid.UUID, payload: RoleUpdate) -> RoleOrm | None:
        role = await self.read_role_by_id(role_id)
        if role is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        await self._session.flush()
        return role

    async def soft_delete_role(self, role_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(RoleOrm)
            .where(RoleOrm.id == role_id, RoleOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(RoleOrm.id)
        )
        return deleted_id is not None

    async def read_role_by_id(self, role_id: uuid.UUID) -> RoleOrm | None:
        return await self._session.scalar(
            select(RoleOrm).where(RoleOrm.id == role_id, RoleOrm.deleted_at.is_(None))
        )

    async def read_role_by_code(self, code: str) -> RoleOrm | None:
        return await self._session.scalar(
            select(RoleOrm).where(RoleOrm.code == code, RoleOrm.deleted_at.is_(None))
        )

    async def count_roles(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(RoleOrm).where(RoleOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_roles(self, *, offset: int, limit: int) -> list[RoleOrm]:
        statement: Select[tuple[RoleOrm]] = (
            select(RoleOrm)
            .where(RoleOrm.deleted_at.is_(None))
            .order_by(RoleOrm.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
