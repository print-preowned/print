from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.privilege.orm import PrivilegeOrm
from app.privilege.schemas import PrivilegeCreate, PrivilegeUpdate


class PrivilegeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_privilege(self, payload: PrivilegeCreate) -> PrivilegeOrm:
        privilege = PrivilegeOrm(**payload.model_dump())
        self._session.add(privilege)
        await self._session.flush()
        return privilege

    async def update_privilege(
        self, privilege_id: uuid.UUID, payload: PrivilegeUpdate
    ) -> PrivilegeOrm | None:
        privilege = await self.read_privilege_by_id(privilege_id)
        if privilege is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(privilege, field, value)
        await self._session.flush()
        return privilege

    async def soft_delete_privilege(self, privilege_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(PrivilegeOrm)
            .where(PrivilegeOrm.id == privilege_id, PrivilegeOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(PrivilegeOrm.id)
        )
        return deleted_id is not None

    async def soft_delete_privilege_by_code(self, code: str) -> bool:
        deleted_id = await self._session.scalar(
            update(PrivilegeOrm)
            .where(PrivilegeOrm.code == code, PrivilegeOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(PrivilegeOrm.id)
        )
        return deleted_id is not None

    async def read_privilege_by_id(self, privilege_id: uuid.UUID) -> PrivilegeOrm | None:
        return await self._session.scalar(
            select(PrivilegeOrm).where(
                PrivilegeOrm.id == privilege_id, PrivilegeOrm.deleted_at.is_(None)
            )
        )

    async def read_privilege_by_code(self, code: str) -> PrivilegeOrm | None:
        return await self._session.scalar(
            select(PrivilegeOrm).where(PrivilegeOrm.code == code, PrivilegeOrm.deleted_at.is_(None))
        )

    async def read_privileges_by_module_name(self, module_name: str) -> list[PrivilegeOrm]:
        result = await self._session.scalars(
            select(PrivilegeOrm).where(
                PrivilegeOrm.module_name == module_name, PrivilegeOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def count_privileges(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(PrivilegeOrm).where(PrivilegeOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_privileges(self, *, offset: int, limit: int) -> list[PrivilegeOrm]:
        statement: Select[tuple[PrivilegeOrm]] = (
            select(PrivilegeOrm)
            .where(PrivilegeOrm.deleted_at.is_(None))
            .order_by(PrivilegeOrm.module_name, PrivilegeOrm.code)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
