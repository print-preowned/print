from app.book_genre.model import (
    BookGenre,
    BookGenreCreateRequest,
    BookGenreUpdateRequest,
)
from .service import (
    delete_service,
    delete_by_book_and_genre_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
    read_by_book_id_service,
    read_by_genre_id_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from fastapi import APIRouter, Response

router = APIRouter(prefix="/book-genre", tags=["BookGenreController"])


@router.post("/create")
async def create(payload: BookGenreCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: BookGenreUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.delete("/delete/by-book/{book_id}/genre/{genre_id}")
async def delete_by_book_and_genre(book_id: str, genre_id: str) -> Response:
    return await delete_by_book_and_genre_service(book_id, genre_id)


@router.get("/read")
async def read(
    page: int = 1, size: int = 5, search: str | None = None
) -> PaginatedResponse[BookGenre]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[BookGenre]:
    return await read_by_id_service(id)


@router.get("/read/by-book/{book_id}")
async def read_by_book_id(book_id: str) -> BaseResponse[list[BookGenre]]:
    return await read_by_book_id_service(book_id)


@router.get("/read/by-genre/{genre_id}")
async def read_by_genre_id(genre_id: str) -> BaseResponse[list[BookGenre]]:
    return await read_by_genre_id_service(genre_id)


