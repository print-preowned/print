from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_user.orm import PlatformUserOrm
from app.platform_user.schemas import PlatformUserCreate, PlatformUserUpdate


class PlatformUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_platform_user(self, payload: PlatformUserCreate) -> PlatformUserOrm:
        platform_user = PlatformUserOrm(**payload.model_dump())
        self._session.add(platform_user)
        await self._session.flush()
        return platform_user

    async def update_platform_user(
        self, platform_user_id: uuid.UUID, payload: PlatformUserUpdate
    ) -> PlatformUserOrm | None:
        platform_user = await self.read_platform_user_by_id(platform_user_id)
        if platform_user is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(platform_user, field, value)
        await self._session.flush()
        return platform_user

    async def soft_delete_platform_user(self, platform_user_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(PlatformUserOrm)
            .where(PlatformUserOrm.id == platform_user_id, PlatformUserOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(PlatformUserOrm.id)
        )
        return deleted_id is not None

    async def read_platform_user_by_id(self, platform_user_id: uuid.UUID) -> PlatformUserOrm | None:
        return await self._session.scalar(
            select(PlatformUserOrm).where(
                PlatformUserOrm.id == platform_user_id, PlatformUserOrm.deleted_at.is_(None)
            )
        )

    async def read_platform_user_by_user_id(self, user_id: uuid.UUID) -> PlatformUserOrm | None:
        return await self._session.scalar(
            select(PlatformUserOrm).where(
                PlatformUserOrm.user_id == user_id, PlatformUserOrm.deleted_at.is_(None)
            )
        )

    async def read_active_by_privilege_set_id(
        self, privilege_set_id: uuid.UUID
    ) -> PlatformUserOrm | None:
        return await self._session.scalar(
            select(PlatformUserOrm).where(
                PlatformUserOrm.platform_privilege_set_id == privilege_set_id,
                PlatformUserOrm.status == "ACTIVE",
                PlatformUserOrm.deleted_at.is_(None),
            )
        )

    async def count_platform_users(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(PlatformUserOrm)
            .where(PlatformUserOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_platform_users(self, *, offset: int, limit: int) -> list[PlatformUserOrm]:
        statement: Select[tuple[PlatformUserOrm]] = (
            select(PlatformUserOrm)
            .where(PlatformUserOrm.deleted_at.is_(None))
            .order_by(PlatformUserOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
