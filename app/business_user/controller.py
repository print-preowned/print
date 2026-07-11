from fastapi import APIRouter, Depends, HTTPException, Response

from app.business_user.model import BusinessUserCreateRequest, BusinessUserUpdateRequest
from app.business_user.schemas import BusinessUserRead
from app.business_user.service import ReadableBusinessUserService, WritableBusinessUserService
from app.utility.authorization import TokenPayload, get_business_id, require_privilege
from app.utility.model import BaseResponse

router = APIRouter(prefix="/business-users", tags=["business-users"])


def _business_id(token: TokenPayload) -> str:
    business_id = get_business_id(token)
    if not business_id:
        raise HTTPException(status_code=403, detail="Business context required")
    return business_id


@router.post("", status_code=201)
async def create(
    payload: BusinessUserCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_BUSINESS_USER")),
    service: WritableBusinessUserService = Depends(),
) -> Response:
    return await service.create(payload)


@router.patch("/{id}")
async def update(
    id: str,
    payload: BusinessUserUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_BUSINESS_USER")),
    service: WritableBusinessUserService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/{id}")
async def delete(
    id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_BUSINESS_USER")),
    service: WritableBusinessUserService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("")
async def read_by_business_id(
    token: TokenPayload = Depends(require_privilege("READ_BUSINESS_USER")),
    service: ReadableBusinessUserService = Depends(),
) -> BaseResponse[list[BusinessUserRead]]:
    return await service.read_by_business_id(_business_id(token))


@router.get("/{id}")
async def read_by_id(
    id: str,
    token: TokenPayload = Depends(require_privilege("READ_BUSINESS_USER")),
    service: ReadableBusinessUserService = Depends(),
) -> BaseResponse[BusinessUserRead]:
    return await service.read_by_id(id)
