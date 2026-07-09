from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.password_reset_token.repository import PasswordResetTokenRepository
from app.password_reset_token.schemas import PasswordResetTokenCreate, PasswordResetTokenRead
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _parse_id(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


def _to_read(row) -> PasswordResetTokenRead:
    return PasswordResetTokenRead.model_validate(row)


async def create_query(
    user_id: str | uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> str:
    async with get_sessionmaker()() as session:
        created = await PasswordResetTokenRepository(session).create_password_reset_token(
            PasswordResetTokenCreate(
                user_id=_parse_id(user_id),
                token_hash=token_hash,
                expires_at=expires_at,
            ),
        )
        await session.commit()
        return str(created.id)


async def read_by_token_hash_query(token_hash: str) -> PasswordResetTokenRead | None:
    async with get_sessionmaker()() as session:
        row = await PasswordResetTokenRepository(session).read_password_reset_token_by_hash(
            token_hash
        )
    return _to_read(row) if row else None


async def mark_as_used_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        marked = await PasswordResetTokenRepository(session).mark_password_reset_token_used(
            parsed_id
        )
        if not marked:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)
