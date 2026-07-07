from fastapi import HTTPException, Response
from app.book_author.model import BookAuthorCreateRequest, BookAuthorUpdateRequest
from app.book_author.schemas import BookAuthorRead
from .query import (
    delete_query,
    delete_by_book_and_author_query,
    read_query,
    read_by_id_query,
    create_query,
    update_query,
    read_by_book_id_query,
    read_by_author_id_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(mapping: BookAuthorCreateRequest) -> Response:
    await create_query(mapping)
    return Response(status_code=201)


async def update_service(id: str, mapping: BookAuthorUpdateRequest) -> Response:
    update = await update_query(id, mapping)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return Response(status_code=204)


async def delete_by_book_and_author_service(
    book_id: str, author_id: str
) -> Response:
    deleted = await delete_by_book_and_author_query(book_id, author_id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[BookAuthorRead]:
    mappings = await read_query(params)
    return PaginatedResponse[BookAuthorRead](
        status_code=200,
        message="Successful",
        data=mappings.data,
        pagination=mappings.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[BookAuthorRead]:
    mapping = await read_by_id_query(id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return BaseResponse[BookAuthorRead](status_code=200, message="Successful", data=mapping)


async def read_by_book_id_service(book_id: str) -> BaseResponse[list[BookAuthorRead]]:
    data = await read_by_book_id_query(book_id)
    return BaseResponse[list[BookAuthorRead]](status_code=200, message="Successful", data=data)


async def read_by_author_id_service(author_id: str) -> BaseResponse[list[BookAuthorRead]]:
    data = await read_by_author_id_query(author_id)
    return BaseResponse[list[BookAuthorRead]](status_code=200, message="Successful", data=data)


