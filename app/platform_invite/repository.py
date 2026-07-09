from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_invite.orm import PlatformInviteOrm
from app.platform_invite.schemas import PlatformInviteCreate


class PlatformInviteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_platform_invite(
        self,
        *,
        payload: PlatformInviteCreate,
        token_hash: str,
        invited_by: uuid.UUID,
        expires_at: datetime,
    ) -> PlatformInviteOrm:
        invite = PlatformInviteOrm(
            email=str(payload.email).strip().lower(),
            platform_privilege_set_id=payload.platform_privilege_set_id,
            token_hash=token_hash,
            expires_at=expires_at,
            status="PENDING",
            invited_by=invited_by,
            accepted_at=None,
        )
        self._session.add(invite)
        await self._session.flush()
        return invite

    async def read_platform_invite_by_id(self, invite_id: uuid.UUID) -> PlatformInviteOrm | None:
        return await self._session.scalar(
            select(PlatformInviteOrm).where(PlatformInviteOrm.id == invite_id)
        )

    async def read_platform_invite_by_token_hash(self, token_hash: str) -> PlatformInviteOrm | None:
        return await self._session.scalar(
            select(PlatformInviteOrm).where(PlatformInviteOrm.token_hash == token_hash)
        )

    async def read_pending_invite_by_email(self, email: str) -> PlatformInviteOrm | None:
        normalized = email.strip().lower()
        return await self._session.scalar(
            select(PlatformInviteOrm).where(
                func.lower(PlatformInviteOrm.email) == normalized,
                PlatformInviteOrm.status == "PENDING",
            )
        )

    async def update_invite_status(
        self, invite_id: uuid.UUID, status: str, *, accepted_at: datetime | None = None
    ) -> bool:
        values: dict[str, object] = {"status": status}
        if accepted_at is not None:
            values["accepted_at"] = accepted_at
        updated_id = await self._session.scalar(
            update(PlatformInviteOrm)
            .where(PlatformInviteOrm.id == invite_id)
            .values(**values)
            .returning(PlatformInviteOrm.id)
        )
        return updated_id is not None

    async def resend_pending_invite(
        self,
        invite_id: uuid.UUID,
        *,
        token_hash: str,
        platform_privilege_set_id: uuid.UUID,
        expires_at: datetime,
    ) -> bool:
        updated_id = await self._session.scalar(
            update(PlatformInviteOrm)
            .where(PlatformInviteOrm.id == invite_id, PlatformInviteOrm.status == "PENDING")
            .values(
                token_hash=token_hash,
                platform_privilege_set_id=platform_privilege_set_id,
                expires_at=expires_at,
            )
            .returning(PlatformInviteOrm.id)
        )
        return updated_id is not None

    async def mark_expired_invites(self) -> int:
        now = datetime.now(UTC)
        expired_ids = await self._session.scalars(
            update(PlatformInviteOrm)
            .where(PlatformInviteOrm.status == "PENDING", PlatformInviteOrm.expires_at < now)
            .values(status="EXPIRED")
            .returning(PlatformInviteOrm.id)
        )
        return len(list(expired_ids))

    async def count_platform_invites(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(PlatformInviteOrm)
            .where(PlatformInviteOrm.status != "EXPIRED")
        )
        return int(total or 0)

    async def list_platform_invites(self, *, offset: int, limit: int) -> list[PlatformInviteOrm]:
        statement: Select[tuple[PlatformInviteOrm]] = (
            select(PlatformInviteOrm)
            .where(PlatformInviteOrm.status != "EXPIRED")
            .order_by(PlatformInviteOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
