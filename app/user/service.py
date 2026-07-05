from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError

from app.business.query import read_by_id_query as read_business_by_id_query
from app.business_user.query import read_one_by_user_id_query
from app.platform_privilege_set_privilege.query import read_by_privilege_set_id_query
from app.platform_user.query import read_by_user_id_query as read_platform_user_by_user_id_query
from app.role.model import Role, OWNER_ROLE_CODE
from app.role.query import read_by_id_query as read_role_by_id_query
from app.role.repository import read_role_by_code as read_role_by_code_pg
from app.role_privilege.query import read_privilege_codes_by_role_id_query
from app.role_privilege.repository import read_privilege_codes_by_role_id as read_privilege_codes_by_role_id_pg
from app.user.model import (
    ContextSwitchResponse,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    UserUpdateRequest,
)
from app.user.orm import UserOrm
from app.user.schemas import UserRead, UserSignup, UserUpdate
from app.utility.authorization import TokenPayload
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, Pagination
from app.utility.postgres import get_sessionmaker
from app.utility.redis import set_key
from app.utility.token import create_business_token, create_customer_token, create_platform_token

from . import repository


def _parse_user_id(user_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


def _to_read(row: UserOrm) -> UserRead:
    return UserRead.model_validate(row)


def _to_user_update(payload: UserUpdateRequest) -> UserUpdate:
    data = payload.model_dump(exclude_unset=True)
    role_id = data.pop("role_id", None)
    if role_id is not None:
        data["role_id"] = uuid.UUID(str(role_id))
    return UserUpdate(**data)


async def login_service(
    request: Request, login_request: LoginRequest, isPlatform: bool = False
) -> LoginResponse:
    async with get_sessionmaker()() as session:
        row = await repository.read_user_by_email(session, login_request.email)
    if row is None:
        raise HTTPException(status_code=403, detail="Invalid credentials")

    user = _to_read(row)
    password_hash = PasswordHash.recommended()
    if not password_hash.verify(login_request.password, user.password):
        raise HTTPException(status_code=403, detail="Invalid credentials")

    request.app.state.authenticated[str(user.email)] = user.first_name

    if isPlatform:
        platform_user = await read_platform_user_by_user_id_query(str(user.id))
        if not platform_user:
            raise HTTPException(
                status_code=403,
                detail="You are not a platform user. Please contact an administrator.",
            )

        privilege_mappings = await read_by_privilege_set_id_query(
            str(platform_user.platform_privilege_set_id)
        )
        privileges = [mapping.privilege_code for mapping in privilege_mappings]
        token = create_platform_token(
            user,
            privileges,
            password_change_required=(user.status == "NEW"),
        )
    else:
        membership = await read_one_by_user_id_query(str(user.id))
        token = create_customer_token(user, has_business=(membership is not None))

    set_key(user.email, token, 60 * 60 * 24)

    return LoginResponse(
        status_code=200,
        message="Successful",
        data=user,
        token=token,
    )


async def signup_service(request: Request, user: SignupRequest) -> LoginResponse:
    async with get_sessionmaker()() as session:
        existing = await repository.read_user_by_email(session, user.email)
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )

        password_hash = PasswordHash.recommended()
        signup_fields = set(UserSignup.model_fields)
        payload = UserSignup.model_validate(
            user.model_copy(update={"password": password_hash.hash(user.password)}).model_dump(
                include=signup_fields
            )
        )
        try:
            created = await repository.signup_user(session, payload)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            ) from exc

    created_user = _to_read(created)
    token = create_customer_token(created_user, has_business=False)
    set_key(created_user.email, token, 60 * 60 * 24)
    request.app.state.authenticated[str(created_user.email)] = created_user.first_name

    return LoginResponse(
        status_code=201,
        message="Successful",
        data=created_user,
        token=token,
    )


async def update_service(id: str, user: UserUpdateRequest) -> Response:
    parsed_id = _parse_user_id(id)
    async with get_sessionmaker()() as session:
        updated = await repository.update_user(session, parsed_id, _to_user_update(user))
        if updated is None:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(status_code=409, detail="Email already in use") from exc
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    parsed_id = _parse_user_id(id)
    async with get_sessionmaker()() as session:
        deleted = await repository.soft_delete_user(session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
        await session.commit()
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[UserRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await repository.count_users(session)
        rows = await repository.list_users(session, offset=offset, limit=size)

    total_pages = math.ceil(total_results / size) if size else 1
    return PaginatedResponse[UserRead](
        status_code=200,
        message="Successful",
        data=[_to_read(row) for row in rows],
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_id_service(id: str) -> BaseResponse[UserRead]:
    parsed_id = _parse_user_id(id)
    async with get_sessionmaker()() as session:
        row = await repository.read_user_by_id(session, parsed_id)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return BaseResponse[UserRead](status_code=200, message="Successful", data=_to_read(row))


async def read_by_role_id_service(role_id: str) -> BaseResponse[list[UserRead]]:
    try:
        parsed_role_id = uuid.UUID(role_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Role not found") from exc

    async with get_sessionmaker()() as session:
        rows = await repository.read_users_by_role_id(session, parsed_role_id)
    return BaseResponse[list[UserRead]](
        status_code=200,
        message="Successful",
        data=[_to_read(row) for row in rows],
    )


async def read_by_email_service(email: str) -> BaseResponse[UserRead]:
    async with get_sessionmaker()() as session:
        row = await repository.read_user_by_email(session, email)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return BaseResponse[UserRead](status_code=200, message="Successful", data=_to_read(row))


async def switch_context_service(
    token_payload: TokenPayload,
    target_context: str,
) -> ContextSwitchResponse:
    if target_context not in ["CUSTOMER", "BUSINESS"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid target context. Must be 'CUSTOMER', 'BUSINESS'",
        )

    if token_payload.ctx == target_context:
        raise HTTPException(
            status_code=400,
            detail=f"You are already in {target_context} context",
        )

    user_id = token_payload.sub
    parsed_user_id = _parse_user_id(user_id)

    async with get_sessionmaker()() as session:
        row = await repository.read_user_by_id(session, parsed_user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    user = _to_read(row)

    if target_context == "BUSINESS":
        membership = await read_one_by_user_id_query(user_id)
        if not membership:
            raise HTTPException(
                status_code=404,
                detail="You don't have a business. Please create one first.",
            )

        business = await read_business_by_id_query(str(membership.business_id))
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        business_id = str(business.id)
        is_owner = str(business.user_id) == user_id
        is_system_role = False

        if is_owner:
            async with get_sessionmaker()() as session:
                owner_role = await read_role_by_code_pg(session, OWNER_ROLE_CODE)
                if owner_role is None:
                    raise HTTPException(
                        status_code=500,
                        detail="Owner role is not configured.",
                    )
                role_id = str(owner_role.id)
                role_name = owner_role.name
                privileges = await read_privilege_codes_by_role_id_pg(session, owner_role.id)
        else:
            role_id = str(membership.role_id)
            role_record = await read_role_by_id_query(role_id)
            role_name = Role.model_validate(role_record).name if role_record else "Member"
            privileges = await read_privilege_codes_by_role_id_query(role_id)

        token = create_business_token(
            user_id,
            business_id,
            role_id,
            role_name,
            is_system_role,
            is_owner,
            privileges,
        )
        message = "Context switched to BUSINESS"
    else:
        token = create_customer_token(user, has_business=True)
        message = "Context switched to CUSTOMER"

    set_key(user.email, token, 60 * 60 * 24)

    return ContextSwitchResponse(
        status_code=200,
        message=message,
        token=token,
    )
