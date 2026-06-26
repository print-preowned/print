from fastapi import HTTPException, Response
from app.variant_option.model import (
    VariantOption,
    VariantOptionCreateRequest,
    VariantOptionUpdateRequest,
)
from .query import delete_query, read_query, read_by_id_query, create_query, update_query
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(item: VariantOptionCreateRequest) -> Response:
    await create_query(item)
    return Response(status_code=201)


async def update_service(id: str, item: VariantOptionUpdateRequest) -> Response:
    update = await update_query(id, item)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="VariantOption not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="VariantOption not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[VariantOption]:
    items = await read_query(params)
    return PaginatedResponse[VariantOption](
        status_code=200,
        message="Successful",
        data=items.data,
        pagination=items.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[VariantOption]:
    item = await read_by_id_query(id)
    if item is None:
        raise HTTPException(status_code=404, detail="VariantOption not found")
    return BaseResponse[VariantOption](status_code=200, message="Successful", data=item)


