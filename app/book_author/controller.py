from app.book_author.model import (
    BookAuthor,
    BookAuthorCreateRequest,
    BookAuthorUpdateRequest,
)
from .service import (
    delete_service,
    delete_by_book_and_author_service,
    read_service,
    read_by_id_service,
    create_service,
    update_service,
    read_by_book_id_service,
    read_by_author_id_service,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest
from fastapi import APIRouter, Response

router = APIRouter(prefix="/book-author", tags=["BookAuthorController"])


@router.post("/create")
async def create(payload: BookAuthorCreateRequest) -> Response:
    return await create_service(payload)


@router.put("/update/{id}")
async def update(id: str, payload: BookAuthorUpdateRequest) -> Response:
    return await update_service(id, payload)


@router.delete("/delete/{id}")
async def delete(id) -> Response:
    return await delete_service(id)


@router.delete("/delete/by-book/{book_id}/author/{author_id}")
async def delete_by_book_and_author(book_id: str, author_id: str) -> Response:
    return await delete_by_book_and_author_service(book_id, author_id)


@router.get("/read")
async def read(
    page: int = 1, size: int = 5, search: str | None = None
) -> PaginatedResponse[BookAuthor]:
    param = ParamRequest(page=page, size=size, search=search)
    return await read_service(param)


@router.get("/read/by-id/{id}")
async def read_by_id(id: str) -> BaseResponse[BookAuthor]:
    return await read_by_id_service(id)


@router.get("/read/by-book/{book_id}")
async def read_by_book_id(book_id: str) -> BaseResponse[list[BookAuthor]]:
    return await read_by_book_id_service(book_id)


@router.get("/read/by-author/{author_id}")
async def read_by_author_id(author_id: str) -> BaseResponse[list[BookAuthor]]:
    return await read_by_author_id_service(author_id)


