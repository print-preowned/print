from fastapi import HTTPException, Response
from app.order.model import Order, OrderCreateRequest, OrderUpdateRequest
from .query import delete_query, read_query, read_by_id_query, create_query, update_query
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(order: OrderCreateRequest) -> Response:
    await create_query(order)
    return Response(status_code=201)


async def update_service(id: str, order: OrderUpdateRequest) -> Response:
    update = await update_query(id, order)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return Response(status_code=200)


async def delete_service(id: str) -> Response:
    deleted = await delete_query(id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[Order]:
    orders = await read_query(params)
    return PaginatedResponse[Order](
        status_code=200,
        message="Successful",
        data=orders.data,
        pagination=orders.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[Order]:
    order = await read_by_id_query(id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return BaseResponse[Order](status_code=200, message="Successful", data=order)


