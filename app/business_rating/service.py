from fastapi import HTTPException, Response
from app.business_rating.model import BusinessRatingCreateRequest, BusinessRatingUpdateRequest
from app.business_rating.schemas import BusinessRatingRead
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    create_query,
    update_query,
    read_by_business_id_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(rating: BusinessRatingCreateRequest) -> Response:
    await create_query(rating)
    return Response(status_code=201)


async def update_service(id: str, rating: BusinessRatingUpdateRequest) -> Response:
    update = await update_query(id, rating)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rating not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rating not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[BusinessRatingRead]:
    ratings = await read_query(params)
    return PaginatedResponse[BusinessRatingRead](
        status_code=200,
        message="Successful",
        data=ratings.data,
        pagination=ratings.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[BusinessRatingRead]:
    rating = await read_by_id_query(id)
    if rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    return BaseResponse[BusinessRatingRead](status_code=200, message="Successful", data=rating)


async def read_by_business_id_service(business_id: str) -> BaseResponse[list[BusinessRatingRead]]:
    data = await read_by_business_id_query(business_id)
    return BaseResponse[list[BusinessRatingRead]](status_code=200, message="Successful", data=data)


