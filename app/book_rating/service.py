from fastapi import HTTPException, Response
from app.book_rating.model import (
    BookRating,
    BookRatingCreateRequest,
    BookRatingUpdateRequest,
)
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    create_query,
    update_query,
    read_by_book_id_query,
    read_by_user_id_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(rating: BookRatingCreateRequest) -> Response:
    await create_query(rating)
    return Response(status_code=201)


async def update_service(id: str, rating: BookRatingUpdateRequest) -> Response:
    update = await update_query(id, rating)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rating not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Rating not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[BookRating]:
    ratings = await read_query(params)
    return PaginatedResponse[BookRating](
        status_code=200,
        message="Successful",
        data=ratings.data,
        pagination=ratings.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[BookRating]:
    rating = await read_by_id_query(id)
    if rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    return BaseResponse[BookRating](status_code=200, message="Successful", data=rating)


async def read_by_book_id_service(book_id: str) -> BaseResponse[list[BookRating]]:
    data = await read_by_book_id_query(book_id)
    return BaseResponse[list[BookRating]](status_code=200, message="Successful", data=data)


async def read_by_user_id_service(user_id: str) -> BaseResponse[list[BookRating]]:
    data = await read_by_user_id_query(user_id)
    return BaseResponse[list[BookRating]](status_code=200, message="Successful", data=data)


