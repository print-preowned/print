from fastapi import APIRouter, Depends, Response

from app.book_author.model import BookAuthorCreateRequest, BookAuthorUpdateRequest
from app.book_author.schemas import BookAuthorRead
from app.book_author.service import ReadableBookAuthorService, WritableBookAuthorService
from app.utility.authorization import TokenPayload, require_privilege
from app.utility.model import BaseResponse

router = APIRouter(prefix="/books/{book_id}/authors", tags=["book-authors"])
author_router = APIRouter(prefix="/authors/{author_id}/books", tags=["book-authors"])


@router.post("", status_code=201)
async def create(
    book_id: str,
    payload: BookAuthorCreateRequest,
    token: TokenPayload = Depends(require_privilege("CREATE_BOOK_AUTHOR")),
    service: WritableBookAuthorService = Depends(),
) -> Response:
    return await service.create(book_id, payload)


@router.patch("/{id}")
async def update(
    book_id: str,
    id: str,
    payload: BookAuthorUpdateRequest,
    token: TokenPayload = Depends(require_privilege("UPDATE_BOOK_AUTHOR")),
    service: WritableBookAuthorService = Depends(),
) -> Response:
    return await service.update(book_id, id, payload)


@router.delete("/{author_id}")
async def delete_by_book_and_author(
    book_id: str,
    author_id: str,
    token: TokenPayload = Depends(require_privilege("DELETE_BOOK_AUTHOR")),
    service: WritableBookAuthorService = Depends(),
) -> Response:
    return await service.delete_by_book_and_author(book_id, author_id)


@router.get("")
async def read_by_book_id(
    book_id: str,
    token: TokenPayload = Depends(require_privilege("READ_BOOK_AUTHOR")),
    service: ReadableBookAuthorService = Depends(),
) -> BaseResponse[list[BookAuthorRead]]:
    return await service.read_by_book_id(book_id)


@author_router.get("")
async def read_by_author_id(
    author_id: str,
    token: TokenPayload = Depends(require_privilege("READ_BOOK_AUTHOR")),
    service: ReadableBookAuthorService = Depends(),
) -> BaseResponse[list[BookAuthorRead]]:
    return await service.read_by_author_id(author_id)
