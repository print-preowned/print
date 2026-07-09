from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service
from app.variant_type.model import VariantTypeCreateRequest, VariantTypeUpdateRequest
from app.variant_type.repository import VariantTypeRepository
from app.variant_type.schemas import ProductOptionCreate, ProductOptionRead, ProductOptionUpdate


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> ProductOptionRead:
    return ProductOptionRead.model_validate(row)


class VariantTypeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = VariantTypeRepository(session)

    async def create(self, item: VariantTypeCreateRequest) -> Response:
        payload = ProductOptionCreate.model_validate(item.model_dump())
        await self._repo.create_product_option(payload)
        return Response(status_code=201)

    async def update(self, id: str, item: VariantTypeUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        updated = await self._repo.update_product_option(
            parsed_id,
            ProductOptionUpdate.model_validate(item.model_dump(exclude_unset=True)),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="VariantType not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_product_option(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="VariantType not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[ProductOptionRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_product_options()
        rows = await self._repo.list_product_options(offset=offset, limit=size)

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
        row = await self._repo.read_product_option_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="VariantType not found")
        return BaseResponse[ProductOptionRead](
            status_code=200, message="Successful", data=_to_read(row)
        )


class WritableVariantTypeService(writable_service(VariantTypeService)):
    pass


class ReadableVariantTypeService(readable_service(VariantTypeService)):
    pass
