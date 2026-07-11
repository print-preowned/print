from fastapi import APIRouter, Depends, Response

from app.book_rating.model import BookRatingCreateRequest
from app.book_rating.schemas import BookRatingRead
from app.book_rating.service import ReadableBookRatingService, WritableBookRatingService
from app.utility.authorization import TokenPayload, require_context
from app.utility.model import BaseResponse

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("", status_code=201)
async def create(
    payload: BookRatingCreateRequest,
    token: TokenPayload = Depends(require_context("CUSTOMER")),
    service: WritableBookRatingService = Depends(),
) -> Response:
    return await service.create(payload)


@router.get("/books/{book_id}")
async def read_by_book_id(
    book_id: str,
    service: ReadableBookRatingService = Depends(),
) -> BaseResponse[list[BookRatingRead]]:
    return await service.read_by_book_id(book_id)


@router.get("/{id}")
async def read_by_id(
    id: str,
    service: ReadableBookRatingService = Depends(),
) -> BaseResponse[BookRatingRead]:
    return await service.read_by_id(id)
