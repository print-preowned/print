from __future__ import annotations

import hashlib
import math
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.platform_invite.model import PlatformInviteCreateRequest
from app.platform_invite.repository import PlatformInviteRepository
from app.platform_invite.schemas import PlatformInviteCreate, PlatformInviteRead
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformInviteRead:
    return PlatformInviteRead.model_validate(row)


async def read_pending_by_email_query(email: str) -> PlatformInviteRead | None:
    async with get_sessionmaker()() as session:
        row = await PlatformInviteRepository(session).read_pending_invite_by_email(email)
    return _to_read(row) if row else None


async def resend_pending_query(
    id: str,
    *,
    token_hash: str,
    platform_privilege_set_id: uuid.UUID | str,
    expires_at: datetime,
    updated_by: str,
) -> bool:
    parsed_id = _parse_id(id)
    parsed_set_id = uuid.UUID(str(platform_privilege_set_id))
    async with get_sessionmaker()() as session:
        updated = await PlatformInviteRepository(session).resend_pending_invite(
            parsed_id,
            token_hash=token_hash,
            platform_privilege_set_id=parsed_set_id,
            expires_at=expires_at,
        )
        if updated:
            await session.commit()
    return updated


async def create_query(
    invite: PlatformInviteCreateRequest,
    token_hash: str,
    invited_by: str,
    expires_at: datetime,
) -> uuid.UUID:
    payload = PlatformInviteCreate(
        email=invite.email,
        platform_privilege_set_id=uuid.UUID(str(invite.platform_privilege_set_id)),
    )
    async with get_sessionmaker()() as session:
        created = await PlatformInviteRepository(session).create_platform_invite(
            payload=payload,
            token_hash=token_hash,
            invited_by=uuid.UUID(str(invited_by)),
            expires_at=expires_at,
        )
        await session.commit()
        return created.id


async def read_query(params: ParamRequest) -> PaginatedData[PlatformInviteRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await PlatformInviteRepository(session).count_platform_invites()
        rows = await PlatformInviteRepository(session).list_platform_invites(
            offset=offset, limit=size
        )

    total_pages = math.ceil(total_results / size) if size else 1
    return PaginatedData(
        data=[_to_read(row) for row in rows],
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_id_query(id: str) -> PlatformInviteRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await PlatformInviteRepository(session).read_platform_invite_by_id(parsed_id)
    return _to_read(row) if row else None


async def read_by_token_hash_query(token_hash: str) -> PlatformInviteRead | None:
    async with get_sessionmaker()() as session:
        row = await PlatformInviteRepository(session).read_platform_invite_by_token_hash(token_hash)
    return _to_read(row) if row else None


async def update_status_query(
    id: str,
    status: str,
    accepted_at: datetime | None = None,
) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await PlatformInviteRepository(session).update_invite_status(
            parsed_id,
            status,
            accepted_at=accepted_at,
        )
        if not updated:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def mark_expired_query() -> UpdateResult:
    async with get_sessionmaker()() as session:
        count = await PlatformInviteRepository(session).mark_expired_invites()
        if count:
            await session.commit()
    return UpdateResult(matched_count=count)
