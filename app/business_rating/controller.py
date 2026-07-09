from fastapi import APIRouter, Depends, Response

from app.business_rating.model import BusinessRatingCreateRequest, BusinessRatingUpdateRequest
from app.business_rating.schemas import BusinessRatingRead
from app.business_rating.service import ReadableBusinessRatingService, WritableBusinessRatingService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/business-rating", tags=["BusinessRatingController"])


@router.post("/create")
async def create(
    payload: BusinessRatingCreateRequest,
    service: WritableBusinessRatingService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: BusinessRatingUpdateRequest,
    service: WritableBusinessRatingService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableBusinessRatingService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableBusinessRatingService = Depends(),
) -> PaginatedResponse[BusinessRatingRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableBusinessRatingService = Depends(),
) -> BaseResponse[BusinessRatingRead]:
    return await service.read_by_id(id)


@router.get("/read/by-business/{business_id}")
async def read_by_business_id(
    business_id: str,
    service: ReadableBusinessRatingService = Depends(),
) -> BaseResponse[list[BusinessRatingRead]]:
    return await service.read_by_business_id(business_id)
