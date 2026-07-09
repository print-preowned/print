from fastapi import APIRouter, Depends, Response

from app.book_author.model import BookAuthorCreateRequest, BookAuthorUpdateRequest
from app.book_author.schemas import BookAuthorRead
from app.book_author.service import ReadableBookAuthorService, WritableBookAuthorService
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest

router = APIRouter(prefix="/book-author", tags=["BookAuthorController"])


@router.post("/create")
async def create(
    payload: BookAuthorCreateRequest,
    service: WritableBookAuthorService = Depends(),
) -> Response:
    return await service.create(payload)


@router.put("/update/{id}")
async def update(
    id: str,
    payload: BookAuthorUpdateRequest,
    service: WritableBookAuthorService = Depends(),
) -> Response:
    return await service.update(id, payload)


@router.delete("/delete/{id}")
async def delete(
    id: str,
    service: WritableBookAuthorService = Depends(),
) -> Response:
    return await service.delete(id)


@router.delete("/delete/by-book/{book_id}/author/{author_id}")
async def delete_by_book_and_author(
    book_id: str,
    author_id: str,
    service: WritableBookAuthorService = Depends(),
) -> Response:
    return await service.delete_by_book_and_author(book_id, author_id)


@router.get("/read")
async def read(
    page: int = 1,
    size: int = 5,
    search: str | None = None,
    service: ReadableBookAuthorService = Depends(),
) -> PaginatedResponse[BookAuthorRead]:
    param = ParamRequest(page=page, size=size, search=search)
    return await service.read(param)


@router.get("/read/by-id/{id}")
async def read_by_id(
    id: str,
    service: ReadableBookAuthorService = Depends(),
) -> BaseResponse[BookAuthorRead]:
    return await service.read_by_id(id)


@router.get("/read/by-book/{book_id}")
async def read_by_book_id(
    book_id: str,
    service: ReadableBookAuthorService = Depends(),
) -> BaseResponse[list[BookAuthorRead]]:
    return await service.read_by_book_id(book_id)


@router.get("/read/by-author/{author_id}")
async def read_by_author_id(
    author_id: str,
    service: ReadableBookAuthorService = Depends(),
) -> BaseResponse[list[BookAuthorRead]]:
    return await service.read_by_author_id(author_id)
