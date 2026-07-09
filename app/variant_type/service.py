from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.variant_type.model import VariantTypeCreateRequest, VariantTypeUpdateRequest
from app.variant_type.repository import (
    count_product_options,
    create_product_option,
    list_product_options,
    read_product_option_by_id,
    soft_delete_product_option,
    update_product_option,
)
from app.variant_type.schemas import ProductOptionCreate, ProductOptionRead, ProductOptionUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> ProductOptionRead:
    return ProductOptionRead.model_validate(row)


class VariantTypeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item: VariantTypeCreateRequest) -> Response:
        payload = ProductOptionCreate.model_validate(item.model_dump())
        await create_product_option(self._session, payload)
        return Response(status_code=201)

    async def update(self, id: str, item: VariantTypeUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        updated = await update_product_option(
            self._session,
            parsed_id,
            ProductOptionUpdate.model_validate(item.model_dump(exclude_unset=True)),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="VariantType not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await soft_delete_product_option(self._session, parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="VariantType not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[ProductOptionRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_product_options(self._session)
        rows = await list_product_options(self._session, offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[ProductOptionRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[ProductOptionRead]:
        parsed_id = _parse_id(id)
        row = await read_product_option_by_id(self._session, parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="VariantType not found")
        return BaseResponse[ProductOptionRead](status_code=200, message="Successful", data=_to_read(row))


from app.utility.service_deps import readable_service, writable_service

WritableVariantTypeService = writable_service(VariantTypeService)
ReadableVariantTypeService = readable_service(VariantTypeService)
