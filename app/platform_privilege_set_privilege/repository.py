from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_privilege_set_privilege.orm import PlatformPrivilegeSetPrivilegeOrm
from app.platform_privilege_set_privilege.schemas import (
    PlatformPrivilegeSetPrivilegeCreate,
    PlatformPrivilegeSetPrivilegeUpdate,
)


class PlatformPrivilegeSetPrivilegeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_platform_privilege_set_privilege(
        self, payload: PlatformPrivilegeSetPrivilegeCreate
    ) -> PlatformPrivilegeSetPrivilegeOrm:
        mapping = PlatformPrivilegeSetPrivilegeOrm(**payload.model_dump())
        self._session.add(mapping)
        await self._session.flush()
        return mapping

    async def update_platform_privilege_set_privilege(
        self, mapping_id: uuid.UUID, payload: PlatformPrivilegeSetPrivilegeUpdate
    ) -> PlatformPrivilegeSetPrivilegeOrm | None:
        mapping = await self.read_platform_privilege_set_privilege_by_id(mapping_id)
        if mapping is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(mapping, field, value)
        await self._session.flush()
        return mapping

    async def soft_delete_platform_privilege_set_privilege(self, mapping_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(PlatformPrivilegeSetPrivilegeOrm)
            .where(
                PlatformPrivilegeSetPrivilegeOrm.id == mapping_id,
                PlatformPrivilegeSetPrivilegeOrm.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(PlatformPrivilegeSetPrivilegeOrm.id)
        )
        return deleted_id is not None

    async def soft_delete_by_privilege_set_and_code(
        self, privilege_set_id: uuid.UUID, privilege_code: str
    ) -> bool:
        deleted_id = await self._session.scalar(
            update(PlatformPrivilegeSetPrivilegeOrm)
            .where(
                PlatformPrivilegeSetPrivilegeOrm.privilege_set_id == privilege_set_id,
                PlatformPrivilegeSetPrivilegeOrm.privilege_code == privilege_code,
                PlatformPrivilegeSetPrivilegeOrm.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(PlatformPrivilegeSetPrivilegeOrm.id)
        )
        return deleted_id is not None

    async def read_platform_privilege_set_privilege_by_id(
        self, mapping_id: uuid.UUID
    ) -> PlatformPrivilegeSetPrivilegeOrm | None:
        return await self._session.scalar(
            select(PlatformPrivilegeSetPrivilegeOrm).where(
                PlatformPrivilegeSetPrivilegeOrm.id == mapping_id,
                PlatformPrivilegeSetPrivilegeOrm.deleted_at.is_(None),
            )
        )

    async def read_by_privilege_set_and_code(
        self, privilege_set_id: uuid.UUID, privilege_code: str
    ) -> PlatformPrivilegeSetPrivilegeOrm | None:
        return await self._session.scalar(
            select(PlatformPrivilegeSetPrivilegeOrm).where(
                PlatformPrivilegeSetPrivilegeOrm.privilege_set_id == privilege_set_id,
                PlatformPrivilegeSetPrivilegeOrm.privilege_code == privilege_code,
                PlatformPrivilegeSetPrivilegeOrm.deleted_at.is_(None),
            )
        )

    async def read_by_privilege_set_id(
        self, privilege_set_id: uuid.UUID
    ) -> list[PlatformPrivilegeSetPrivilegeOrm]:
        result = await self._session.scalars(
            select(PlatformPrivilegeSetPrivilegeOrm).where(
                PlatformPrivilegeSetPrivilegeOrm.privilege_set_id == privilege_set_id,
                PlatformPrivilegeSetPrivilegeOrm.deleted_at.is_(None),
            )
        )
        return list(result)

    async def count_platform_privilege_set_privileges(self) -> int:
        from sqlalchemy import func

        total = await self._session.scalar(
            select(func.count())
            .select_from(PlatformPrivilegeSetPrivilegeOrm)
            .where(PlatformPrivilegeSetPrivilegeOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_platform_privilege_set_privileges(
        self, *, offset: int, limit: int
    ) -> list[PlatformPrivilegeSetPrivilegeOrm]:
        from sqlalchemy import Select

        statement: Select[tuple[PlatformPrivilegeSetPrivilegeOrm]] = (
            select(PlatformPrivilegeSetPrivilegeOrm)
            .where(PlatformPrivilegeSetPrivilegeOrm.deleted_at.is_(None))
            .order_by(
                PlatformPrivilegeSetPrivilegeOrm.privilege_set_id,
                PlatformPrivilegeSetPrivilegeOrm.privilege_code,
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
