from fastapi import HTTPException, Request, Response
from app.platform_user.model import (
    PlatformUserCreateRequest,
    PlatformUserSignupRequest,
    PlatformUserUpdateRequest,
    PlatformUserWithUser,
)
from app.platform_user.schemas import PlatformUserRead
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
from app.user.model import LoginRequest, LoginResponse, SignupRequest, UserCreateRequest
from app.user.query import signup_query, read_by_ids_query as read_users_by_ids
from app.platform_privilege_set.query import read_by_ids_query as read_privilege_sets_by_ids
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
            status="ACTIVE",
        )
    )
    return Response(status_code=201)


async def login_service(request: Request, user: LoginRequest) -> LoginResponse:
    response = await user_login_service(request, user, True)
    print(f"=======> response: {response}")
    return response
 


async def create_service(platform_user: PlatformUserCreateRequest) -> Response:
    existing = await read_by_user_id_query(str(platform_user.user_id))
    if existing:
        raise HTTPException(
            status_code=409,
            detail="User already has a platform user record"
        )

    await ensure_super_admin_not_invitable(str(platform_user.platform_privilege_set_id))
    
    await create_query(platform_user)
    return Response(status_code=201)


async def update_service(id: str, platform_user: PlatformUserUpdateRequest) -> Response:
    existing = await read_by_id_query(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Platform user not found")

    if platform_user.platform_privilege_set_id is not None:
        new_privilege_set_id = platform_user.platform_privilege_set_id
        await ensure_super_admin_not_demoted(existing, new_privilege_set_id)
        await ensure_super_admin_not_assignable_via_update(str(new_privilege_set_id))

    update = await update_query(id, platform_user)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform user not found")
    return Response(status_code=200)


async def transfer_super_admin_service(
    caller_user_id: str,
    target_platform_user_id: str,
) -> Response:
    caller_platform_user = await ensure_caller_is_super_admin(caller_user_id)

    if str(caller_platform_user.id) == target_platform_user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot transfer the super admin role to yourself",
        )

    target = await read_by_id_query(target_platform_user_id)
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

    await update_query(
        str(caller_platform_user.id),
        PlatformUserUpdateRequest(platform_privilege_set_id=admin_set_id),
    )
    await update_query(
        target_platform_user_id,
        PlatformUserUpdateRequest(platform_privilege_set_id=super_admin_set_id),
    )
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    existing = await read_by_id_query(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Platform user not found")

    await ensure_super_admin_not_removed(existing)

    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Platform user not found")
    return Response(status_code=204)


async def _populate_platform_user_with_user(
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


async def read_me_service(user_id: str) -> BaseResponse[PlatformUserWithUser]:
    platform_user = await read_by_user_id_query(user_id)
    if platform_user is None:
        raise HTTPException(status_code=404, detail="Platform user not found")
    return BaseResponse[PlatformUserWithUser](
        status_code=200,
        message="Successful",
        data=await _populate_platform_user_with_user(platform_user),
    )


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
    privilege_set_ids = list(
        {str(pu.platform_privilege_set_id) for pu in platform_users.data}
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
    for pu in platform_users.data:
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
    return PaginatedResponse[PlatformUserWithUser](
        status_code=200,
        message="Successful",
        data=data,
        pagination=platform_users.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[PlatformUserRead]:
    platform_user = await read_by_id_query(id)
    if platform_user is None:
        raise HTTPException(status_code=404, detail="Platform user not found")
    return BaseResponse[PlatformUserRead](status_code=200, message="Successful", data=platform_user)


async def read_by_user_id_service(user_id: str) -> BaseResponse[PlatformUserRead | None]:
    platform_user = await read_by_user_id_query(user_id)
    return BaseResponse[PlatformUserRead | None](status_code=200, message="Successful", data=platform_user)
