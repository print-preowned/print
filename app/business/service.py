from fastapi import HTTPException
from fastapi.responses import Response
from app.business.model import Business, BusinessCreateRequest, BusinessCreateResponse, BusinessUpdateRequest
from .query import delete_query, read_query, read_by_id_query, create_query, update_query, read_by_user_id_query
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest, PyObjectId
from app.business_user.service import create_service as create_business_user_service
from app.business_user.model import BusinessUserCreateRequest
from app.role.service import read_owner_role_service
from app.user.query import read_by_id_query as read_user_by_id_query
from app.user.model import User
from app.utility.token import create_customer_token


async def create_service(business: BusinessCreateRequest, user_id: str) -> BusinessCreateResponse:
    user_record = await read_user_by_id_query(user_id)
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")
    user = User.model_validate(user_record)

    existing_business = await read_by_user_id_query(user_id)
    if existing_business:
        raise HTTPException(
            status_code=409,
            detail="You already have a business. Each user can only create one business."
        )
    
    business.user_id = PyObjectId(user_id)
    
    # Create the business
    await create_query(business)
    
    # Get the created business ID
    created_business = await read_by_user_id_query(user_id)
    if not created_business:
        raise HTTPException(status_code=500, detail="Failed to retrieve created business")
    
    business_id = created_business.id
    
    # Get the Owner role by code (must exist - standard roles are created separately)
    owner_role_response = await read_owner_role_service()
    owner_role = owner_role_response.data
    
    if not owner_role:
        raise HTTPException(
            status_code=404,
            detail="Owner role not found. Please ensure standard roles are created."
        )
    
    role_id = owner_role.id
    
    # Create business_user record with owner role
    business_user = BusinessUserCreateRequest(
        business_id=business_id,
        user_id=PyObjectId(user_id),
        role_id=role_id,
        status="ACTIVE"
    )
    await create_business_user_service(business_user)

    # Issue new CUSTOMER token with has_business=True so the client sees "Switch to Business" without re-login
    new_token = create_customer_token(user, has_business=True)
    return BusinessCreateResponse(token=new_token)


async def update_service(id: str, business: BusinessUpdateRequest) -> Response:
    update = await update_query(id, business)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Business not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Business not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[Business]:
    businesses = await read_query(params)
    return PaginatedResponse[Business](
        status_code=200,
        message="Successful",
        data=businesses.data,
        pagination=businesses.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[Business]:
    business = await read_by_id_query(id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return BaseResponse[Business](status_code=200, message="Successful", data=business)


async def read_by_user_id_service(user_id: str) -> BaseResponse[Business | None]:
    """
    Check if a user has a business
    Returns the business if found, None otherwise
    """
    business = await read_by_user_id_query(user_id)
    return BaseResponse[Business | None](status_code=200, message="Successful", data=business)


