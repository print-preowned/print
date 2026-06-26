from datetime import datetime, timezone
from fastapi import HTTPException, Response
from app.business_book.model import (
    BusinessBook,
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithBook,
)
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    read_by_business_id_query,
    create_query,
    update_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def create_service(item: BusinessBookCreateRequest, business_id: str) -> Response:
    # Enforce business_id from token (MDC-BOOK-3: business_book is business-scoped)
    from bson import ObjectId
    data = item.model_dump()
    data["business_id"] = ObjectId(business_id)
    data["created_at"] = data["updated_at"] = datetime.now(timezone.utc)
    data["status"] = "ACTIVE"
    from ..utility.database import get_database
    db = get_database()
    await db["business_book"].insert_one(data)
    return Response(status_code=201)


async def update_service(
    id: str, item: BusinessBookUpdateRequest, business_id: str
) -> Response:
    existing = await read_by_id_query(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="BusinessBook not found")
    if str(existing.business_id) != business_id:
        raise HTTPException(status_code=403, detail="Cannot update another business's listing")
    update = await update_query(id, item)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="BusinessBook not found")
    return Response(status_code=200)


async def delete_service(id: str, business_id: str) -> Response:
    existing = await read_by_id_query(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="BusinessBook not found")
    if str(existing.business_id) != business_id:
        raise HTTPException(status_code=403, detail="Cannot delete another business's listing")
    deleted = await delete_query(id)
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[BusinessBook]:
    items = await read_query(params)
    return PaginatedResponse[BusinessBook](
        status_code=200,
        message="Successful",
        data=items.data,
        pagination=items.pagination,
    )


async def read_by_business_id_service(
    business_id: str, params: ParamRequest
) -> PaginatedResponse[BusinessBookWithBook]:
    result = await read_by_business_id_query(business_id, params)
    return PaginatedResponse[BusinessBookWithBook](
        status_code=200,
        message="Successful",
        data=result.data,
        pagination=result.pagination,
    )


async def read_by_id_service(id: str, business_id: str | None = None) -> BaseResponse[BusinessBook]:
    item = await read_by_id_query(id)
    if item is None:
        raise HTTPException(status_code=404, detail="BusinessBook not found")
    if business_id and str(item.business_id) != business_id:
        raise HTTPException(status_code=403, detail="Not your business listing")
    return BaseResponse[BusinessBook](status_code=200, message="Successful", data=item)


