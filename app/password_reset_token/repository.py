from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.password_reset_token.orm import PasswordResetTokenOrm
from app.password_reset_token.schemas import PasswordResetTokenCreate


async def create_password_reset_token(
    session: AsyncSession,
    payload: PasswordResetTokenCreate,
) -> PasswordResetTokenOrm:
    row = PasswordResetTokenOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def read_password_reset_token_by_hash(
    session: AsyncSession,
    token_hash: str,
) -> PasswordResetTokenOrm | None:
    return await session.scalar(
        select(PasswordResetTokenOrm).where(PasswordResetTokenOrm.token_hash == token_hash)
    )


async def mark_password_reset_token_used(session: AsyncSession, token_id: uuid.UUID) -> bool:
    used_id = await session.scalar(
        update(PasswordResetTokenOrm)
        .where(PasswordResetTokenOrm.id == token_id, PasswordResetTokenOrm.used.is_(False))
        .values(used=True, used_at=datetime.now(UTC))
        .returning(PasswordResetTokenOrm.id)
    )
    return used_id is not None
