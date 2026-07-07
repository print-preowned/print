from fastapi import HTTPException, Response
from app.book_genre.model import BookGenreCreateRequest, BookGenreUpdateRequest
from app.book_genre.schemas import BookGenreRead
from .query import (
    delete_query,
    delete_by_book_and_genre_query,
    read_query,
    read_by_id_query,
    create_query,
    update_query,
    read_by_book_id_query,
    read_by_genre_id_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(mapping: BookGenreCreateRequest) -> Response:
    await create_query(mapping)

    return Response(status_code=201)


async def update_service(id: str, mapping: BookGenreUpdateRequest) -> Response:
    update = await update_query(id, mapping)

    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")

    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)

    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")

    return Response(status_code=204)


async def delete_by_book_and_genre_service(
    book_id: str, genre_id: str
) -> Response:
    deleted = await delete_by_book_and_genre_query(book_id, genre_id)

    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")

    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[BookGenreRead]:
    mappings = await read_query(params)
    response = PaginatedResponse[BookGenreRead](
        status_code=200,
        message="Successful",
        data=mappings.data,
        pagination=mappings.pagination,
    )

    return response


async def read_by_id_service(id: str) -> BaseResponse[BookGenreRead]:
    mapping = await read_by_id_query(id)

    if mapping is None:
        raise HTTPException(status_code=404, detail="Mapping not found")

    response = BaseResponse[BookGenreRead](
        status_code=200, message="Successful", data=mapping
    )

    return response


async def read_by_book_id_service(book_id: str) -> BaseResponse[list[BookGenreRead]]:
    data = await read_by_book_id_query(book_id)
    return BaseResponse[list[BookGenreRead]](status_code=200, message="Successful", data=data)


async def read_by_genre_id_service(genre_id: str) -> BaseResponse[list[BookGenreRead]]:
    data = await read_by_genre_id_query(genre_id)
    return BaseResponse[list[BookGenreRead]](status_code=200, message="Successful", data=data)


