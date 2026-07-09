from fastapi import APIRouter, Depends, Response

from app.book_genre.model import BookGenreCreateRequest, BookGenreUpdateRequest
from app.book_genre.schemas import BookGenreRead
from app.book_genre.service import ReadableBookGenreService, WritableBookGenreService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/book-genre", tags=["BookGenreController"])


@router.post("/create")
async def create(
    payload: BookGenreCreateRequest,
    service: WritableBookGenreService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: BookGenreUpdateRequest,
    service: WritableBookGenreService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableBookGenreService = Depends(),
) -> Response:
    return await service.delete(id)


@router.delete("/delete/by-book/{book_id}/genre/{genre_id}")
async def delete_by_book_and_genre(
    book_id: str,
    genre_id: str,
    service: WritableBookGenreService = Depends(),
) -> Response:
    return await service.delete_by_book_and_genre(book_id, genre_id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableBookGenreService = Depends(),
) -> PaginatedResponse[BookGenreRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableBookGenreService = Depends(),
) -> BaseResponse[BookGenreRead]:
    return await service.read_by_id(id)


@router.get("/read/by-book/{book_id}")
async def read_by_book_id(
    book_id: str,
    service: ReadableBookGenreService = Depends(),
) -> BaseResponse[list[BookGenreRead]]:
    return await service.read_by_book_id(book_id)


@router.get("/read/by-genre/{genre_id}")
async def read_by_genre_id(
    genre_id: str,
    service: ReadableBookGenreService = Depends(),
) -> BaseResponse[list[BookGenreRead]]:
    return await service.read_by_genre_id(genre_id)
