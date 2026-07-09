from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_privilege_set.query import read_by_ids_query as read_privilege_sets_by_ids
from app.platform_user.guards import (
    ensure_caller_is_super_admin,
    ensure_super_admin_not_assignable_via_update,
    ensure_super_admin_not_demoted,
    ensure_super_admin_not_invitable,
    ensure_super_admin_not_removed,
    get_admin_privilege_set_id,
    get_super_admin_privilege_set_id,
    is_super_admin_privilege_set,
)
from app.platform_user.model import (
    PlatformUserCreateRequest,
    PlatformUserSignupRequest,
    PlatformUserUpdateRequest,
    PlatformUserWithUser,
)
from app.platform_user.repository import (
    count_platform_users,
    create_platform_user,
    list_platform_users,
    read_platform_user_by_id,
    read_platform_user_by_user_id,
    soft_delete_platform_user,
    update_platform_user,
)
from app.platform_user.schemas import PlatformUserCreate, PlatformUserRead, PlatformUserUpdate
from app.user.model import LoginRequest, LoginResponse
from app.user.query import read_by_ids_query as read_users_by_ids
from app.user.query import signup_query
from app.user.service import UserService
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> PlatformUserRead:
    return PlatformUserRead.model_validate(row)


def _to_create(payload: PlatformUserCreateRequest) -> PlatformUserCreate:
    return PlatformUserCreate(
        user_id=uuid.UUID(str(payload.user_id)),
        platform_privilege_set_id=uuid.UUID(str(payload.platform_privilege_set_id)),
    )


def _to_update(payload: PlatformUserUpdateRequest) -> PlatformUserUpdate:
    data = payload.model_dump(exclude_unset=True)
    if "platform_privilege_set_id" in data and data["platform_privilege_set_id"] is not None:
        data["platform_privilege_set_id"] = uuid.UUID(str(data["platform_privilege_set_id"]))
    return PlatformUserUpdate(**data)


class PlatformUserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def signup(self, user: PlatformUserSignupRequest) -> Response:
        user_id = await signup_query(user)

        await self.create(
            PlatformUserCreateRequest(
                user_id=user_id,
                platform_privilege_set_id=user.platform_privilege_set_id,
                status="ACTIVE",
            )
        )
        return Response(status_code=201)

    async def login(self, request: Request, user: LoginRequest) -> LoginResponse:
        return await UserService(self._session).login(request, user, True)

    async def create(self, platform_user: PlatformUserCreateRequest) -> Response:
        existing = await read_platform_user_by_user_id(
            self._session,
            uuid.UUID(str(platform_user.user_id)),
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="User already has a platform user record",
            )

        await ensure_super_admin_not_invitable(str(platform_user.platform_privilege_set_id))

        await create_platform_user(self._session, _to_create(platform_user))
        return Response(status_code=201)

    async def update(self, id: str, platform_user: PlatformUserUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        existing_row = await read_platform_user_by_id(self._session, parsed_id)
        if existing_row is None:
            raise HTTPException(status_code=404, detail="Platform user not found")
        existing = _to_read(existing_row)

        if platform_user.platform_privilege_set_id is not None:
            new_privilege_set_id = platform_user.platform_privilege_set_id
            await ensure_super_admin_not_demoted(existing, new_privilege_set_id)
            await ensure_super_admin_not_assignable_via_update(str(new_privilege_set_id))

        updated = await update_platform_user(self._session, parsed_id, _to_update(platform_user))
        if updated is None:
            raise HTTPException(status_code=404, detail="Platform user not found")
        return Response(status_code=200)

    async def transfer_super_admin(
        self,
        caller_user_id: str,
        target_platform_user_id: str,
    ) -> Response:
        caller_platform_user = await ensure_caller_is_super_admin(caller_user_id)

        if str(caller_platform_user.id) == target_platform_user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot transfer the super admin role to yourself",
            )

        target = await read_platform_user_by_id(self._session, _parse_id(target_platform_user_id))
        if target is None:
            raise HTTPException(status_code=404, detail="Platform user not found")

        if await is_super_admin_privilege_set(str(target.platform_privilege_set_id)):
            raise HTTPException(status_code=409, detail="Target user is already the super admin")

        super_admin_set_id = await get_super_admin_privilege_set_id()
        admin_set_id = await get_admin_privilege_set_id()
        if super_admin_set_id is None or admin_set_id is None:
            raise HTTPException(
                status_code=500,
                detail="Required privilege sets not found; cannot transfer super admin role",
            )

        caller_updated = await update_platform_user(
            self._session,
            caller_platform_user.id,
            PlatformUserUpdate(platform_privilege_set_id=uuid.UUID(admin_set_id)),
        )
        if caller_updated is None:
            raise HTTPException(status_code=404, detail="Platform user not found")

        target_updated = await update_platform_user(
            self._session,
            _parse_id(target_platform_user_id),
            PlatformUserUpdate(platform_privilege_set_id=uuid.UUID(super_admin_set_id)),
        )
        if target_updated is None:
            raise HTTPException(status_code=404, detail="Platform user not found")

        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        existing_row = await read_platform_user_by_id(self._session, parsed_id)
        if existing_row is None:
            raise HTTPException(status_code=404, detail="Platform user not found")
        existing = _to_read(existing_row)

        await ensure_super_admin_not_removed(existing)

        deleted = await soft_delete_platform_user(self._session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Platform user not found")
        return Response(status_code=204)

    async def _populate_platform_user_with_user(
        self,
        platform_user: PlatformUserRead,
    ) -> PlatformUserWithUser:
        user_docs = await read_users_by_ids([str(platform_user.user_id)])
        privilege_set_docs = await read_privilege_sets_by_ids(
            [str(platform_user.platform_privilege_set_id)]
        )
        user = user_docs[0] if user_docs else None
        privilege_set = privilege_set_docs[0] if privilege_set_docs else None
        super_admin_set_id = await get_super_admin_privilege_set_id()
        is_super_admin = (
            super_admin_set_id is not None
            and str(platform_user.platform_privilege_set_id) == super_admin_set_id
        )
        return PlatformUserWithUser(
            **platform_user.model_dump(mode="json"),
            user_email=user.email if user else None,
            user_name=(
                f"{user.first_name} {user.last_name}".strip() if user else None
            ),
            platform_privilege_set_name=privilege_set.name if privilege_set else None,
            is_super_admin=is_super_admin,
        )

    async def read_me(self, user_id: str) -> BaseResponse[PlatformUserWithUser]:
        row = await read_platform_user_by_user_id(self._session, _parse_id(user_id))
        if row is None:
            raise HTTPException(status_code=404, detail="Platform user not found")
        platform_user = _to_read(row)
        return BaseResponse[PlatformUserWithUser](
            status_code=200,
            message="Successful",
            data=await self._populate_platform_user_with_user(platform_user),
        )

    async def read(self, params: ParamRequest) -> PaginatedResponse[PlatformUserWithUser]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_platform_users(self._session)
        rows = await list_platform_users(self._session, offset=offset, limit=size)
        platform_users = [_to_read(row) for row in rows]

        if not platform_users:
            total_pages = math.ceil(total_results / size) if size else 1
            return PaginatedResponse[PlatformUserWithUser](
                status_code=200,
                message="Successful",
                data=[],
                pagination=Pagination(
                    page=page,
                    size=size,
                    total_pages=total_pages,
                    total_results=total_results,
                ),
            )

        user_ids = [str(pu.user_id) for pu in platform_users]
        privilege_set_ids = list(
            {str(pu.platform_privilege_set_id) for pu in platform_users}
        )
        user_docs = await read_users_by_ids(user_ids)
        privilege_set_docs = await read_privilege_sets_by_ids(privilege_set_ids)
        user_map = {}
        for u in user_docs:
            uid = str(u.id)
            user_map[uid] = {
                "email": u.email or "",
                "name": f"{u.first_name} {u.last_name}".strip() or "—",
            }
        privilege_set_map = {
            str(ps.id): ps.name for ps in privilege_set_docs
        }
        super_admin_set_id = await get_super_admin_privilege_set_id()
        data = []
        for pu in platform_users:
            info = user_map.get(str(pu.user_id), {"email": "—", "name": "—"})
            privilege_set_name = privilege_set_map.get(
                str(pu.platform_privilege_set_id), "—"
            )
            is_super_admin = (
                super_admin_set_id is not None
                and str(pu.platform_privilege_set_id) == super_admin_set_id
            )
            data.append(
                PlatformUserWithUser(
                    **pu.model_dump(mode="json"),
                    user_email=info["email"],
                    user_name=info["name"],
                    platform_privilege_set_name=privilege_set_name,
                    is_super_admin=is_super_admin,
                )
            )

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[PlatformUserWithUser](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str) -> BaseResponse[PlatformUserRead]:
        row = await read_platform_user_by_id(self._session, _parse_id(id))
        if row is None:
            raise HTTPException(status_code=404, detail="Platform user not found")
        return BaseResponse[PlatformUserRead](status_code=200, message="Successful", data=_to_read(row))

    async def read_by_user_id(self, user_id: str) -> BaseResponse[PlatformUserRead | None]:
        row = await read_platform_user_by_user_id(self._session, _parse_id(user_id))
        return BaseResponse[PlatformUserRead | None](
            status_code=200,
            message="Successful",
            data=_to_read(row) if row else None,
        )


class WritablePlatformUserService(writable_service(PlatformUserService)):
    pass


class ReadablePlatformUserService(readable_service(PlatformUserService)):
    pass
