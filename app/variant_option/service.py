from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.variant_option.model import VariantOptionCreateRequest, VariantOptionUpdateRequest
from app.variant_option.repository import (
    count_product_option_values,
    create_product_option_value,
    list_product_option_values,
    read_product_option_value_by_id,
    soft_delete_product_option_value,
    update_product_option_value,
)
from app.variant_option.schemas import (
    ProductOptionValueCreate,
    ProductOptionValueRead,
    ProductOptionValueUpdate,
)
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> ProductOptionValueRead:
    return ProductOptionValueRead.model_validate(row)


def _to_create(payload: VariantOptionCreateRequest) -> ProductOptionValueCreate:
    return ProductOptionValueCreate(
        product_option_id=uuid.UUID(str(payload.variant_type_id)),
        value=payload.value,
    )


def _to_update(payload: VariantOptionUpdateRequest) -> ProductOptionValueUpdate:
    data = payload.model_dump(exclude_unset=True)
    if "variant_type_id" in data and data["variant_type_id"] is not None:
        data["product_option_id"] = uuid.UUID(str(data.pop("variant_type_id")))
    return ProductOptionValueUpdate(**data)


class VariantOptionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item: VariantOptionCreateRequest) -> Response:
        await create_product_option_value(self._session, _to_create(item))
        return Response(status_code=201)

    async def update(self, id: str, item: VariantOptionUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        updated = await update_product_option_value(self._session, parsed_id, _to_update(item))
        if updated is None:
            raise HTTPException(status_code=404, detail="VariantOption not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await soft_delete_product_option_value(self._session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="VariantOption not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[ProductOptionValueRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_product_option_values(self._session)
        rows = await list_product_option_values(self._session, offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[ProductOptionValueRead](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_variant_type(
        self,
        variant_type_id: str,
        params: ParamRequest,
    ) -> PaginatedResponse[ProductOptionValueRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        parsed_option_id = _parse_id(variant_type_id)

        total_results = await count_product_option_values(
            self._session,
            product_option_id=parsed_option_id,
        )
        rows = await list_product_option_values(
            self._session,
            offset=offset,
            limit=size,
            product_option_id=parsed_option_id,
        )

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[ProductOptionValueRead](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str) -> BaseResponse[ProductOptionValueRead]:
        parsed_id = _parse_id(id)
        row = await read_product_option_value_by_id(self._session, parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="VariantOption not found")
        return BaseResponse[ProductOptionValueRead](
            status_code=200,
            message="Successful",
            data=_to_read(row),
        )


from app.utility.service_deps import readable_service, writable_service

WritableVariantOptionService = writable_service(VariantOptionService)
ReadableVariantOptionService = readable_service(VariantOptionService)
