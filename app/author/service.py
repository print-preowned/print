from fastapi import HTTPException, Response
from fastapi.responses import JSONResponse
from app.author.model import Author, AuthorCreateRequest, AuthorUpdateRequest
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    create_query,
    update_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(author: AuthorCreateRequest) -> Response:
    inserted_id = await create_query(author)
    return JSONResponse(
        status_code=201,
        content={"id": str(inserted_id), "message": "Author created"},
    )


async def update_service(id: str, author: AuthorUpdateRequest) -> Response:
    update = await update_query(id, author)

    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Author not found")

    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)

    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Author not found")

    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[Author]:
    authors = await read_query(params)
    response = PaginatedResponse[Author](
        status_code=200,
        message="Successful",
        data=authors.data,
        pagination=authors.pagination,
    )

    return response


async def read_by_id_service(id: str) -> BaseResponse[Author]:
    author = await read_by_id_query(id)

    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    response = BaseResponse[Author](status_code=200, message="Successful", data=author)

    return response
