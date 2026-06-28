from fastapi import HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
import jwt
from app.user.model import LoginRequest, LoginResponse, SignupRequest, User, UserCreateRequest, UserUpdateRequest, ContextSwitchRequest, ContextSwitchResponse
from app.utility.redis import set_key
from app.utility.token import create_customer_token, create_business_token, create_platform_token
from app.business.query import read_by_user_id_query, read_by_id_query as read_business_by_id_query
from app.business_user.query import read_one_by_user_id_query
from app.role.query import read_by_id_query as read_role_by_id_query
from app.role.model import Role
from app.role_privilege.query import read_privilege_codes_by_role_id_query
from app.platform_user.query import read_by_user_id_query as read_platform_user_by_user_id_query
from app.platform_privilege_set_privilege.query import read_by_privilege_set_id_query
from .query import (
    delete_query,
    read_by_email_query,
    read_query,
    read_by_id_query,
    create_query,
    signup_query,
    update_query,
    read_by_role_id_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest, PyObjectId
from ..utility.authorization import TokenPayload
from pwdlib import PasswordHash


async def login_service(request: Request, login_request: LoginRequest, isPlatform: bool = False) -> LoginResponse:
    user = (await read_by_email_query(login_request.email))
    if user is None:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    
    try: 
        password_hash = PasswordHash.recommended()
        is_valid = password_hash.verify(login_request.password, user.password)
        if is_valid is False:
            raise HTTPException(status_code=403, detail="Invalid credentials")

    except Exception as e: 
        raise e

    
    # Store a key-value pair for the logged-in user
    user_key = str(user.email) if hasattr(user, "email") else user.id
    request.app.state.authenticated[user_key] = user.first_name
    
    # Create token following PRINT Authorization & Context Model
    if isPlatform:
        # Check if user is a platform user and get their privileges
        platform_user = await read_platform_user_by_user_id_query(str(user.id))
        print("=======> platform_user", platform_user)
        if not platform_user:
            raise HTTPException(
                status_code=403,
                detail="You are not a platform user. Please contact an administrator."
            )
        
        # Get all privilege mappings for the privilege set
        privilege_mappings = await read_by_privilege_set_id_query(str(platform_user.platform_privilege_set_id))
        
        # Extract privilege codes from mappings
        privileges = [mapping.privilege_code for mapping in privilege_mappings]
        
        # Create platform token with privileges
        token = create_platform_token(
            user,
            privileges,
            password_change_required=(user.status == "NEW"),
        )
    else:
        # Create CUSTOMER context token; include has_business so client can show "Switch to Business" without a round trip.
        # Owners and staff are both in business_user, so one check is enough.
        membership = await read_one_by_user_id_query(str(user.id))
        token = create_customer_token(user, has_business=(membership is not None))
    
    set_key(user.email, token, 60 * 60 * 24)

    return LoginResponse(
        status_code=200,
        message="Successful",
        data=user,
        token=token
    )


async def signup_service(request: Request, user: SignupRequest) -> LoginResponse:
    existing = await read_by_email_query(user.email)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )
    password_hash = PasswordHash.recommended()
    password = password_hash.hash(user.password)
    user_id = await signup_query(user.model_copy(update={"password": password}))

    record = await read_by_id_query(user_id)
    if not record:
        raise HTTPException(status_code=500, detail="User creation failed.")
    created_user = User.model_validate(record)
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
    update = await update_query(id, user)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[User]:
    users = await read_query(params)
    return PaginatedResponse[User](
        status_code=200,
        message="Successful",
        data=users.data,
        pagination=users.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[User]:
    user = await read_by_id_query(id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return BaseResponse[User](status_code=200, message="Successful", data=user)


async def read_by_role_id_service(role_id: str) -> BaseResponse[list[User]]:
    data = await read_by_role_id_query(role_id)
    return BaseResponse[list[User]](status_code=200, message="Successful", data=data)


async def read_by_email_service(email: str) -> BaseResponse[User]:
    data = await read_by_email_query(email)
    if data is None:
        raise HTTPException(status_code=404, detail="User not found")
    return BaseResponse[User](status_code=200, message="Successful", data=data)


async def switch_context_service(
    token_payload: TokenPayload,
    target_context: str
) -> ContextSwitchResponse:
    """
    Switch context between CUSTOMER and BUSINESS
    
    Following MDC-CONTEXT-3: token_reissue_on_context_switch
    - Issues a new access token
    - Old token must be discarded (handled by client)
    - Validates that current context is not the same as target context
    """
    # Validate target context
    if target_context not in ["CUSTOMER", "BUSINESS"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid target context. Must be 'CUSTOMER', 'BUSINESS'"
        )
    
    # Check that current context is not the same as target context
    if token_payload.ctx == target_context:
        raise HTTPException(
            status_code=400,
            detail=f"You are already in {target_context} context"
        )
    
    user_id = token_payload.sub
    
    # Get user object for token creation
    user = await read_by_id_query(user_id)
    print("=======> user", user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_context == "BUSINESS":
        # Switch to BUSINESS context: resolve business by ownership (business.user_id) or membership (business_user)
        business = await read_by_user_id_query(user_id)
        is_owner = business is not None
        membership = None
        if not business:
            membership = await read_one_by_user_id_query(user_id)
            if membership:
                business = await read_business_by_id_query(str(membership.business_id))
        if not business:
            raise HTTPException(
                status_code=404,
                detail="You don't have a business. Please create one first."
            )

        business_id = str(business.id)
        if is_owner:
            role_id = "owner-role-id"
            role_name = "Owner"
            is_system_role = False
            privileges = [
                "READ_USER", "CREATE_USER", "UPDATE_USER", "DELETE_USER",
                "READ_BOOK", "CREATE_BOOK", "UPDATE_BOOK", "DELETE_BOOK",
                "READ_AUTHOR", "CREATE_AUTHOR", "UPDATE_AUTHOR",
                "READ_INVENTORY", "CREATE_INVENTORY_ITEM", "UPDATE_INVENTORY_ITEM", "DELETE_INVENTORY_ITEM",
                "READ_ORDER", "UPDATE_ORDER_STATUS", "REFUND_ORDER",
                "READ_RATING", "UPDATE_RATING",
            ]
        else:
            if not membership:
                raise HTTPException(status_code=404, detail="Business membership not found.")
            role_id = str(membership.role_id)
            role_record = await read_role_by_id_query(role_id)
            role_name = Role.model_validate(role_record).name if role_record else "Member"
            is_system_role = False
            privileges = await read_privilege_codes_by_role_id_query(role_id)
        
        # Create business token
        token = create_business_token(
            user_id,
            business_id,
            role_id,
            role_name,
            is_system_role,
            is_owner,
            privileges
        )
        
        message = "Context switched to BUSINESS"
    else:
        # Switch to CUSTOMER context (user had a business to switch from)
        token = create_customer_token(user, has_business=True)
        message = "Context switched to CUSTOMER"
    
    # Store token in Redis
    set_key(user.email, token, 60 * 60 * 24)
    
    return ContextSwitchResponse(
        status_code=200,
        message=message,
        token=token
    )

