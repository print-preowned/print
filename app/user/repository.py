from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.orm import UserOrm
from app.user.schemas import UserCreate, UserSignup, UserUpdate


async def create_user(session: AsyncSession, payload: UserCreate) -> UserOrm:
    user = UserOrm(**payload.model_dump())
    session.add(user)
    await session.flush()
    return user


async def signup_user(session: AsyncSession, payload: UserSignup) -> UserOrm:
    user = UserOrm(**payload.model_dump())
    session.add(user)
    await session.flush()
    return user


async def update_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: UserUpdate,
) -> UserOrm | None:
    user = await read_user_by_id(session, user_id)
    if user is None:
        return None

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await session.flush()
    return user


async def soft_delete_user(session: AsyncSession, user_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(UserOrm)
        .where(UserOrm.id == user_id, UserOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC))
        .returning(UserOrm.id)
    )
    return deleted_id is not None


async def read_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> UserOrm | None:
    return await session.scalar(
        select(UserOrm).where(UserOrm.id == user_id, UserOrm.deleted_at.is_(None))
    )


async def read_user_by_email(session: AsyncSession, email: str) -> UserOrm | None:
    normalized = email.strip().lower()
    return await session.scalar(
        select(UserOrm).where(
            func.lower(UserOrm.email) == normalized,
            UserOrm.deleted_at.is_(None),
        )
    )


async def read_users_by_ids(session: AsyncSession, user_ids: list[uuid.UUID]) -> list[UserOrm]:
    if not user_ids:
        return []
    result = await session.scalars(
        select(UserOrm).where(UserOrm.id.in_(user_ids), UserOrm.deleted_at.is_(None))
    )
    return list(result)


async def read_users_by_role_id(session: AsyncSession, role_id: uuid.UUID) -> list[UserOrm]:
    result = await session.scalars(
        select(UserOrm).where(UserOrm.role_id == role_id, UserOrm.deleted_at.is_(None))
    )
    return list(result)


async def count_users(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(UserOrm).where(UserOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_users(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[UserOrm]:
    statement: Select[tuple[UserOrm]] = (
        select(UserOrm)
        .where(UserOrm.deleted_at.is_(None))
        .order_by(UserOrm.last_name, UserOrm.first_name)
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)
