from fastapi import APIRouter, Depends, Response

from app.book_rating.model import BookRatingCreateRequest, BookRatingUpdateRequest
from app.book_rating.schemas import BookRatingRead
from app.book_rating.service import ReadableBookRatingService, WritableBookRatingService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/book-rating", tags=["BookRatingController"])


@router.post("/create")
async def create(
    payload: BookRatingCreateRequest,
    service: WritableBookRatingService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: BookRatingUpdateRequest,
    service: WritableBookRatingService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableBookRatingService = Depends(),
) -> Response:
    return await service.delete(id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableBookRatingService = Depends(),
) -> PaginatedResponse[BookRatingRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableBookRatingService = Depends(),
) -> BaseResponse[BookRatingRead]:
    return await service.read_by_id(id)


@router.get("/read/by-book/{book_id}")
async def read_by_book_id(
    book_id: str,
    service: ReadableBookRatingService = Depends(),
) -> BaseResponse[list[BookRatingRead]]:
    return await service.read_by_book_id(book_id)


@router.get("/read/by-user/{user_id}")
async def read_by_user_id(
    user_id: str,
    service: ReadableBookRatingService = Depends(),
) -> BaseResponse[list[BookRatingRead]]:
    return await service.read_by_user_id(user_id)
