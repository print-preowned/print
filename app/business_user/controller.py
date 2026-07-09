from fastapi import APIRouter, Depends, Response

from app.business_user.model import BusinessUserCreateRequest, BusinessUserUpdateRequest
from app.business_user.schemas import BusinessUserRead
from app.business_user.service import ReadableBusinessUserService, WritableBusinessUserService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/business-user", tags=["BusinessUserController"])


@router.post("/create")
async def create(
    payload: BusinessUserCreateRequest,
    service: WritableBusinessUserService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: BusinessUserUpdateRequest,
    service: WritableBusinessUserService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableBusinessUserService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableBusinessUserService = Depends(),
) -> PaginatedResponse[BusinessUserRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableBusinessUserService = Depends(),
) -> BaseResponse[BusinessUserRead]:
    return await service.read_by_id(id)


@router.get("/read/by-business/{business_id}")
async def read_by_business_id(
    business_id: str,
    service: ReadableBusinessUserService = Depends(),
) -> BaseResponse[list[BusinessUserRead]]:
    return await service.read_by_business_id(business_id)
