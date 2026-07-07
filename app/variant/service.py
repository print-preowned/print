from fastapi import HTTPException, Response
from app.variant.schemas import PublicCatalogVariantRead, VariantRead, VariantWithConfigRead
from app.variant.model import VariantCreateRequest, VariantUpdateRequest
from .query import (
    create_query,
    delete_query,
    read_by_business_book_id_query,
    read_by_id_query,
    read_by_id_with_config_query,
    read_public_catalog_by_id_query,
    read_public_catalog_query,
    read_query,
    update_query,
)
from app.business_book.query import read_by_id_query as read_business_book_by_id_query
from ..utility.model import BaseResponse, PaginatedResponse, ParamRequest


async def _assert_business_book_owned(business_book_id: str, business_id: str):
    bb = await read_business_book_by_id_query(business_book_id)
    if bb is None:
        raise HTTPException(status_code=404, detail="BusinessBook not found")
    if str(bb.business_id) != business_id:
        raise HTTPException(status_code=403, detail="Not your business listing")
    return bb


async def _assert_variant_belongs_to_business_book(
    variant_id: str, business_book_id: str, business_id: str
):
    await _assert_business_book_owned(business_book_id, business_id)
    variant = await read_by_id_query(variant_id)
    if variant is None:
        raise HTTPException(status_code=404, detail="Variant not found")
    if str(variant.business_book_id) != business_book_id:
        raise HTTPException(
            status_code=403, detail="Variant does not belong to this listing"
        )
    return variant



async def create_service(
    business_book_id: str,
    payload: VariantCreateRequest,
    business_id: str,
) -> BaseResponse[dict]:
    await _assert_business_book_owned(business_book_id, business_id)
    variant_id = await create_query(business_book_id, payload)
    return BaseResponse(status_code=201, message="Created", data={"id": variant_id})


async def update_service(
    business_book_id: str,
    variant_id: str,
    payload: VariantUpdateRequest,
    business_id: str,
) -> Response:
    await _assert_variant_belongs_to_business_book(
        variant_id, business_book_id, business_id
    )
    update = await update_query(variant_id, payload)
    if update.matched_count == 0:
        raise HTTPException(status_code=404, detail="Variant not found")
    return Response(status_code=200)


async def delete_service(
    business_book_id: str, variant_id: str, business_id: str
) -> Response:
    await _assert_variant_belongs_to_business_book(
        variant_id, business_book_id, business_id
    )
    deleted = await delete_query(variant_id)
    if deleted.matched_count == 0:
        raise HTTPException(status_code=404, detail="Variant not found")
    return Response(status_code=204)


async def read_service(params: ParamRequest) -> PaginatedResponse[VariantRead]:
    items = await read_query(params)
    return PaginatedResponse[VariantRead](
        status_code=200,
        message="Successful",
        data=items.data,
        pagination=items.pagination,
    )


async def read_scoped_service(
    business_book_id: str, params: ParamRequest, business_id: str
) -> PaginatedResponse[VariantWithConfigRead]:
    await _assert_business_book_owned(business_book_id, business_id)
    items = await read_by_business_book_id_query(business_book_id, params)
    return PaginatedResponse[VariantWithConfigRead](
        status_code=200,
        message="Successful",
        data=items.data,
        pagination=items.pagination,
    )


async def read_by_id_service(id: str) -> BaseResponse[VariantRead]:
    item = await read_by_id_query(id)
    if item is None:
        raise HTTPException(status_code=404, detail="Variant not found")
    return BaseResponse[VariantRead](status_code=200, message="Successful", data=item)


async def read_by_id_with_config_service(
    id: str,
) -> BaseResponse[VariantWithConfigRead]:
    item = await read_by_id_with_config_query(id)
    if item is None:
        raise HTTPException(status_code=404, detail="Variant not found")
    return BaseResponse[VariantWithConfigRead](
        status_code=200, message="Successful", data=item
    )


async def read_public_catalog_service(
    params: ParamRequest,
) -> PaginatedResponse[PublicCatalogVariantRead]:
    items = await read_public_catalog_query(params)
    return PaginatedResponse[PublicCatalogVariantRead](
        status_code=200,
        message="Successful",
        data=items.data,
        pagination=items.pagination,
    )


async def read_public_catalog_by_id_service(
    id: str,
) -> BaseResponse[PublicCatalogVariantRead]:
    item = await read_public_catalog_by_id_query(id)
    if item is None:
        raise HTTPException(status_code=404, detail="Variant not found")
    return BaseResponse[PublicCatalogVariantRead](
        status_code=200, message="Successful", data=item
    )
