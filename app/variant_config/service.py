from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service
from app.variant_config.model import VariantConfigCreateRequest, VariantConfigUpdateRequest
from app.variant_config.repository import VariantConfigRepository
from app.variant_config.schemas import (
    VariantProductOptionValueCreate,
    VariantProductOptionValueRead,
    VariantProductOptionValueUpdate,
)


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> VariantProductOptionValueRead:
    return VariantProductOptionValueRead.model_validate(row)


class VariantConfigService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = VariantConfigRepository(session)

    async def create(self, item: VariantConfigCreateRequest) -> Response:
        payload = VariantProductOptionValueCreate(
            variant_id=uuid.UUID(str(item.variant_id)),
            product_option_value_id=uuid.UUID(str(item.variant_option_id)),
        )
        await self._repo.create_variant_product_option_value(payload)
        return Response(status_code=201)

    async def update(self, id: str, item: VariantConfigUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        updated = await self._repo.update_variant_product_option_value(
            parsed_id,
            VariantProductOptionValueUpdate.model_validate(item.model_dump(exclude_unset=True)),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="VariantConfig not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_variant_product_option_value(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="VariantConfig not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[VariantProductOptionValueRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_variant_product_option_values()
        rows = await self._repo.list_variant_product_option_values(offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[VariantProductOptionValueRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[VariantProductOptionValueRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_variant_product_option_value_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="VariantConfig not found")
        return BaseResponse[VariantProductOptionValueRead](
            status_code=200,
            message="Successful",
            data=_to_read(row),
        )


WritableVariantConfigService = writable_service(VariantConfigService)
ReadableVariantConfigService = readable_service(VariantConfigService)
