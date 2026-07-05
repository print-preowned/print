from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.user.model import SignupRequest, UserCreateRequest, UserUpdateRequest
from app.user.repository import (
    create_user,
    list_users,
    read_user_by_email,
    read_user_by_id,
    read_users_by_ids,
    read_users_by_role_id,
    signup_user,
    soft_delete_user,
    update_user,
    count_users,
)
from app.user.schemas import UserCreate, UserRead, UserSignup, UserUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker


@dataclass
class UpdateResult:
    matched_count: int


def _parse_user_id(user_id: str) -> uuid.UUID:
    return uuid.UUID(user_id)


def _to_user_update(payload: UserUpdateRequest) -> UserUpdate:
    data = payload.model_dump(exclude_unset=True)
    role_id = data.pop("role_id", None)
    if role_id is not None:
        data["role_id"] = uuid.UUID(str(role_id))
    return UserUpdate(**data)


def _to_read(row) -> UserRead:
    return UserRead.model_validate(row)


async def signup_query(user: SignupRequest) -> str:
    signup_fields = set(UserSignup.model_fields)
    payload = UserSignup.model_validate(user.model_dump(include=signup_fields))
    async with get_sessionmaker()() as session:
        created = await signup_user(session, payload)
        await session.commit()
        return str(created.id)


async def create_query(user: UserCreateRequest) -> None:
    payload = UserCreate.model_validate(user.model_dump())
    async with get_sessionmaker()() as session:
        await create_user(session, payload)
        await session.commit()


async def update_query(id: str, user: UserUpdateRequest) -> UpdateResult:
    parsed_id = _parse_user_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_user(session, parsed_id, _to_user_update(user))
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
        return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_user_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_user(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
        return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[UserRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_users(session)
        rows = await list_users(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> UserRead | None:
    async with get_sessionmaker()() as session:
        row = await read_user_by_id(session, _parse_user_id(id))
    return _to_read(row) if row else None


async def read_by_ids_query(ids: list[str]) -> list[UserRead]:
    if not ids:
        return []
    parsed_ids: list[uuid.UUID] = []
    for user_id in ids:
        try:
            parsed_ids.append(uuid.UUID(user_id))
        except ValueError:
            continue
    if not parsed_ids:
        return []
    async with get_sessionmaker()() as session:
        rows = await read_users_by_ids(session, parsed_ids)
    return [_to_read(row) for row in rows]


async def read_by_role_id_query(role_id: str) -> list[UserRead]:
    async with get_sessionmaker()() as session:
        rows = await read_users_by_role_id(session, uuid.UUID(role_id))
    return [_to_read(row) for row in rows]


async def read_by_email_query(email: str) -> UserRead | None:
    async with get_sessionmaker()() as session:
        row = await read_user_by_email(session, email)
    return _to_read(row) if row else None
