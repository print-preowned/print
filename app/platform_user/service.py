import re
from fastapi import HTTPException, Request, Response
from app.platform_user.model import (
    PlatformUser,
    PlatformUserCreateRequest,
    PlatformUserSignupRequest,
    PlatformUserUpdateRequest,
    PlatformUserWithUser,
)
from app.user.model import LoginRequest, LoginResponse, SignupRequest, UserCreateRequest
from app.user.query import signup_query, read_by_ids_query as read_users_by_ids
from app.user.service import login_service as user_login_service
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    create_query,
    update_query,
    read_by_user_id_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def signup_service(user: PlatformUserSignupRequest) -> Response:
    user_id = await signup_query(user)

    await create_service(
        PlatformUserCreateRequest(
            user_id=user_id,
            platform_privilege_set_id=user.platform_privilege_set_id,
            status="ACTIVE"
        )
    )
    return Response(status_code=201)


async def login_service(request: Request, user: LoginRequest) -> LoginResponse:
    response = await user_login_service(request, user, True)
    print(f"=======> response: {response}")
    return response
 

async def create_service(platform_user: PlatformUserCreateRequest) -> Response:
    # Check if user already has a platform_user record
    existing = await read_by_user_id_query(str(platform_user.user_id))
    if existing:
        raise HTTPException(
            status_code=409,
            detail="User already has a platform user record"
        )
    
    await create_query(platform_user)
    return Response(status_code=201)


async def update_service(id: str, platform_user: PlatformUserUpdateRequest) -> Response:
    update = await update_query(id, platform_user)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform user not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform user not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[PlatformUserWithUser]:
    platform_users = await read_query(params)
    if not platform_users.data:
        return PaginatedResponse[PlatformUserWithUser](
            status_code=200,
            message="Successful",
            data=[],
            pagination=platform_users.pagination,
        )
    user_ids = [str(pu.user_id) for pu in platform_users.data]
    user_docs = await read_users_by_ids(user_ids)
    user_map = {}
    for u in user_docs:
        uid = str(u.id)
        user_map[uid] = {
            "email": u.email or "",
            "name": f"{u.first_name} {u.last_name}".strip() or "—",
        }
    data = []
    for pu in platform_users.data:
        info = user_map.get(str(pu.user_id), {"email": "—", "name": "—"})
        data.append(
            PlatformUserWithUser(
                **pu.model_dump(mode="json"),
                user_email=info["email"],
                user_name=info["name"],
            )
        )
    return PaginatedResponse[PlatformUserWithUser](
        status_code=200,
        message="Successful",
        data=data,
        pagination=platform_users.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[PlatformUser]:
    platform_user = await read_by_id_query(id)
    if platform_user is None:
        raise HTTPException(status_code=404, detail="Platform user not found")
    return BaseResponse[PlatformUser](status_code=200, message="Successful", data=platform_user)


async def read_by_user_id_service(user_id: str) -> BaseResponse[PlatformUser | None]:
    platform_user = await read_by_user_id_query(user_id)
    return BaseResponse[PlatformUser | None](status_code=200, message="Successful", data=platform_user)
