from app.book_rating.model import (
    BookRating,
    BookRatingCreateRequest,
    BookRatingUpdateRequest,
)
from .service import (
    delete_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
    read_by_book_id_service,
    read_by_user_id_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from fastapi import APIRouter, Response

router = APIRouter(prefix="/book-rating", tags=["BookRatingController"])


@router.post("/create")
async def create(payload: BookRatingCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: BookRatingUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.get("/read")
async def read(
    page: int = 1, size: int = 5, search: str | None = None
) -> PaginatedResponse[BookRating]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[BookRating]:
    return await read_by_id_service(id)


@router.get("/read/by-book/{book_id}")
async def read_by_book_id(book_id: str) -> BaseResponse[list[BookRating]]:
    return await read_by_book_id_service(book_id)


@router.get("/read/by-user/{user_id}")
async def read_by_user_id(user_id: str) -> BaseResponse[list[BookRating]]:
    return await read_by_user_id_service(user_id)


