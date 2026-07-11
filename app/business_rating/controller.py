from fastapi import APIRouter, Depends, Response

from app.business_rating.model import BusinessRatingCreateRequest, BusinessRatingUpdateRequest
from app.business_rating.schemas import BusinessRatingRead
from app.business_rating.service import ReadableBusinessRatingService, WritableBusinessRatingService
from app.utility.authorization import TokenPayload, require_context, require_privilege
from app.utility.model import BaseResponse

customer_router = APIRouter(prefix="/businesses/{business_id}/ratings", tags=["business-ratings"])
business_router = APIRouter(prefix="/ratings", tags=["business-ratings"])


@customer_router.post("", status_code=201)
async def create(
    business_id: str,
    payload: BusinessRatingCreateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableBusinessRatingService = Depends(),
) -> Response:
    return await service.create(payload)


@customer_router.get("")
async def read_by_business_id(
    business_id: str,
    service: ReadableBusinessRatingService = Depends(),
) -> BaseResponse[list[BusinessRatingRead]]:
    return await service.read_by_business_id(business_id)


@business_router.patch("/{id}")
async def update(
    id: str,
    payload: BusinessRatingUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_RATING")),
    service: WritableBusinessRatingService = Depends(),
) -> Response:
    return await service.update(id, payload)
