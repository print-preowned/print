from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.orm import UserOrm
from app.user.schemas import UserCreate, UserSignup, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_user(self, payload: UserCreate) -> UserOrm:
        user = UserOrm(**payload.model_dump())
        self._session.add(user)
        await self._session.flush()
        return user

    async def signup_user(self, payload: UserSignup) -> UserOrm:
        user = UserOrm(**payload.model_dump())
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_user(self, user_id: uuid.UUID, payload: UserUpdate) -> UserOrm | None:
        user = await self.read_user_by_id(user_id)
        if user is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self._session.flush()
        return user

    async def soft_delete_user(self, user_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(UserOrm)
            .where(UserOrm.id == user_id, UserOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC))
            .returning(UserOrm.id)
        )
        return deleted_id is not None

    async def read_user_by_id(self, user_id: uuid.UUID) -> UserOrm | None:
        return await self._session.scalar(
            select(UserOrm).where(UserOrm.id == user_id, UserOrm.deleted_at.is_(None))
        )

    async def read_user_by_email(self, email: str) -> UserOrm | None:
        normalized = email.strip().lower()
        return await self._session.scalar(
            select(UserOrm).where(
                func.lower(UserOrm.email) == normalized, UserOrm.deleted_at.is_(None)
            )
        )

    async def read_users_by_ids(self, user_ids: list[uuid.UUID]) -> list[UserOrm]:
        if not user_ids:
            return []
        result = await self._session.scalars(
            select(UserOrm).where(UserOrm.id.in_(user_ids), UserOrm.deleted_at.is_(None))
        )
        return list(result)

    async def read_users_by_role_id(self, role_id: uuid.UUID) -> list[UserOrm]:
        result = await self._session.scalars(
            select(UserOrm).where(UserOrm.role_id == role_id, UserOrm.deleted_at.is_(None))
        )
        return list(result)

    async def count_users(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(UserOrm).where(UserOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_users(self, *, offset: int, limit: int) -> list[UserOrm]:
        statement: Select[tuple[UserOrm]] = (
            select(UserOrm)
            .where(UserOrm.deleted_at.is_(None))
            .order_by(UserOrm.last_name, UserOrm.first_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
