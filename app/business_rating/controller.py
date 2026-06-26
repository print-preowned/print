from app.business_rating.model import (
    BusinessRating,
    BusinessRatingCreateRequest,
    BusinessRatingUpdateRequest,
)
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
    read_by_business_id_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from fastapi import APIRouter, Response

router = APIRouter(prefix="/business-rating", tags=["BusinessRatingController"])


@router.post("/create")
async def create(payload: BusinessRatingCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: BusinessRatingUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.get("/read")
async def read(
    page: int = 1, size: int = 5, search: str | None = None
) -> PaginatedResponse[BusinessRating]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[BusinessRating]:
    return await read_by_id_service(id)


@router.get("/read/by-business/{business_id}")
async def read_by_business_id(business_id: str) -> BaseResponse[list[BusinessRating]]:
    return await read_by_business_id_service(business_id)


