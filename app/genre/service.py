from fastapi import HTTPException, Response
from app.genre.model import Genre, GenreCreateRequest, GenreUpdateRequest
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    create_query,
    update_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(genre: GenreCreateRequest) -> Response:
    await create_query(genre)

    return Response(status_code=201)


async def update_service(id: str, genre: GenreUpdateRequest) -> Response:
    update = await update_query(id, genre)

    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Genre not found")

    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)

    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Genre not found")

    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[Genre]:
    genres = await read_query(params)
    response = PaginatedResponse[Genre](
        status_code=200,
        message="Successful",
        data=genres.data,
        pagination=genres.pagination,
    )

    return response


async def read_by_id_service(id: str) -> BaseResponse[Genre]:
    genre = await read_by_id_query(id)

    if genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")

    response = BaseResponse[Genre](status_code=200, message="Successful", data=genre)

    return response


