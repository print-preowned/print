from datetime import datetime, timezone
from fastapi import HTTPException, Response
from app.business_book.model import (
    BusinessBook,
    BusinessBookWithVariants,
    BusinessBookWithVariantSummary,
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    SELLER_MUTABLE_LISTING_STATUSES,
    SELLER_LISTING_STATUS_TRANSITIONS,
)
from .query import (
    delete_query,
    read_query,
    read_by_id_query,
    read_by_id_with_variants_query,
    read_by_business_id_query,
    create_query,
    update_query,
)
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest, PyObjectId


async def create_service(item: BusinessBookCreateRequest, business_id: str) -> Response:
    item.business_id = PyObjectId(business_id)
    item.status = "DRAFT"
    await create_query(item)
    return Response(status_code=201)


async def update_service(
    id: str, item: BusinessBookUpdateRequest, business_id: str
) -> Response:
    existing = await read_by_id_query(id)
    if existing is None:
        raise HTTPException(status_code=404, detail="BusinessBook not found")
    if str(existing.business_id) != business_id:
        raise HTTPException(status_code=403, detail="Cannot update another business's listing")
    if (
        existing.status == "SUSPENDED"
        and item.status is not None
        and item.status != existing.status
    ):
        raise HTTPException(
            status_code=403,
            detail="Suspended listings cannot be reactivated by seller",
        )
    if item.status is not None and item.status not in SELLER_MUTABLE_LISTING_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Listing status must be one of: DRAFT, ACTIVE, INACTIVE",
        )
    if (
        item.status is not None
        and item.status != existing.status
        and item.status
        not in SELLER_LISTING_STATUS_TRANSITIONS.get(existing.status, frozenset())
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change listing status from {existing.status} to {item.status}"
            ),
        )
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
    await delete_query(id)
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
) -> PaginatedResponse[BusinessBookWithVariantSummary]:
    result = await read_by_business_id_query(business_id, params)
    return PaginatedResponse[BusinessBookWithVariantSummary](
        status_code=200,
        message="Successful",
        data=result.data,
        pagination=result.pagination,
    )


async def read_by_id_service(
    id: str, business_id: str | None = None
) -> BaseResponse[BusinessBookWithVariants]:
    item = await read_by_id_with_variants_query(id)
    if item is None:
        raise HTTPException(status_code=404, detail="BusinessBook not found")
    if business_id and str(item.business_id) != business_id:
        raise HTTPException(status_code=403, detail="Not your business listing")
    return BaseResponse[BusinessBookWithVariants](
        status_code=200, message="Successful", data=item
    )


