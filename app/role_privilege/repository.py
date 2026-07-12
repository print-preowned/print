from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.role_privilege.orm import RolePrivilegeOrm
from app.role_privilege.schemas import RolePrivilegeCreate


class RolePrivilegeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_role_privilege(self, payload: RolePrivilegeCreate) -> RolePrivilegeOrm:
        mapping = RolePrivilegeOrm(**payload.model_dump())
        self._session.add(mapping)
        await self._session.flush()
        return mapping

    async def delete_role_privilege(self, mapping_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(RolePrivilegeOrm)
            .where(RolePrivilegeOrm.id == mapping_id, RolePrivilegeOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(RolePrivilegeOrm.id)
        )
        return deleted_id is not None

    async def delete_by_role_and_code(self, role_id: uuid.UUID, privilege_code: str) -> bool:
        deleted_id = await self._session.scalar(
            update(RolePrivilegeOrm)
            .where(
                RolePrivilegeOrm.role_id == role_id,
                RolePrivilegeOrm.privilege_code == privilege_code,
                RolePrivilegeOrm.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(RolePrivilegeOrm.id)
        )
        return deleted_id is not None

    async def read_role_privilege_by_id(self, mapping_id: uuid.UUID) -> RolePrivilegeOrm | None:
        return await self._session.scalar(
            select(RolePrivilegeOrm).where(
                RolePrivilegeOrm.id == mapping_id, RolePrivilegeOrm.deleted_at.is_(None)
            )
        )

    async def read_role_privilege_by_role_and_code(
        self, role_id: uuid.UUID, privilege_code: str
    ) -> RolePrivilegeOrm | None:
        return await self._session.scalar(
            select(RolePrivilegeOrm).where(
                RolePrivilegeOrm.role_id == role_id,
                RolePrivilegeOrm.privilege_code == privilege_code,
                RolePrivilegeOrm.deleted_at.is_(None),
            )
        )

    async def read_by_privilege_code(self, privilege_code: str) -> list[RolePrivilegeOrm]:
        result = await self._session.scalars(
            select(RolePrivilegeOrm).where(
                RolePrivilegeOrm.privilege_code == privilege_code,
                RolePrivilegeOrm.deleted_at.is_(None),
            )
        )
        return list(result)

    async def read_by_role_id(self, role_id: uuid.UUID) -> list[RolePrivilegeOrm]:
        result = await self._session.scalars(
            select(RolePrivilegeOrm)
            .where(
                RolePrivilegeOrm.role_id == role_id,
                RolePrivilegeOrm.deleted_at.is_(None),
            )
            .order_by(RolePrivilegeOrm.created_at.desc())
        )
        return list(result)

    async def read_privilege_codes_by_role_id(self, role_id: uuid.UUID) -> list[str]:
        result = await self._session.scalars(
            select(RolePrivilegeOrm.privilege_code).where(
                RolePrivilegeOrm.role_id == role_id, RolePrivilegeOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def count_role_privileges(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(RolePrivilegeOrm)
            .where(RolePrivilegeOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_role_privileges(self, *, offset: int, limit: int) -> list[RolePrivilegeOrm]:
        statement: Select[tuple[RolePrivilegeOrm]] = (
            select(RolePrivilegeOrm)
            .where(RolePrivilegeOrm.deleted_at.is_(None))
            .order_by(RolePrivilegeOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
