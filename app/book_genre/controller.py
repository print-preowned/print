from fastapi import APIRouter, Depends, Response

from app.book_genre.model import BookGenreCreateRequest
from app.book_genre.schemas import BookGenreRead
from app.book_genre.service import ReadableBookGenreService, WritableBookGenreService
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse

router = APIRouter(prefix="/books/{book_id}/genres", tags=["book-genres"])


@router.post("", status_code=201)
async def create(
    book_id: str,
    payload: BookGenreCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_BOOK_GENRE")),
    service: WritableBookGenreService = Depends(),
) -> Response:
    return await service.create(book_id, payload)


@router.delete("/{genre_id}")
async def delete_by_book_and_genre(
    book_id: str,
    genre_id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_BOOK_GENRE")),
    service: WritableBookGenreService = Depends(),
) -> Response:
    return await service.delete_by_book_and_genre(book_id, genre_id)


@router.get("")
async def read_by_book_id(
    book_id: str,
    token: TokenPayload = Depends(require_privilege("READ_BOOK_GENRE")),
    service: ReadableBookGenreService = Depends(),
) -> BaseResponse[list[BookGenreRead]]:
    return await service.read_by_book_id(book_id)
