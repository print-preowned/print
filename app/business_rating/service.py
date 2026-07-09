from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_rating.model import BusinessRatingCreateRequest, BusinessRatingUpdateRequest
from app.business_rating.repository import BusinessRatingRepository
from app.business_rating.schemas import (
    BusinessRatingCreate,
    BusinessRatingRead,
    BusinessRatingUpdate,
)
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BusinessRatingRead:
    return BusinessRatingRead.model_validate(row)


def _to_create(payload: BusinessRatingCreateRequest) -> BusinessRatingCreate:
    data = payload.model_dump(include=set(BusinessRatingCreate.model_fields.keys()))
    data["business_id"] = _parse_id(str(data["business_id"]))
    data["user_id"] = _parse_id(str(data["user_id"]))
    if data.get("order_item_id") is not None:
        data["order_item_id"] = _parse_id(str(data["order_item_id"]))
    return BusinessRatingCreate.model_validate(data)


class BusinessRatingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BusinessRatingRepository(session)

    async def create(self, rating: BusinessRatingCreateRequest) -> Response:
        await self._repo.create_business_rating(_to_create(rating))
        return Response(status_code=201)

    async def update(self, id: str, rating: BusinessRatingUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        update_data = rating.model_dump(exclude_unset=True)
        if "business_id" in update_data and update_data["business_id"] is not None:
            update_data["business_id"] = _parse_id(str(update_data["business_id"]))
        if "user_id" in update_data and update_data["user_id"] is not None:
            update_data["user_id"] = _parse_id(str(update_data["user_id"]))
        if "order_item_id" in update_data and update_data["order_item_id"] is not None:
            update_data["order_item_id"] = _parse_id(str(update_data["order_item_id"]))

        updated = await self._repo.update_business_rating(
            parsed_id,
            BusinessRatingUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Rating not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_business_rating(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Rating not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BusinessRatingRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_business_ratings()
        rows = await self._repo.list_business_ratings(offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[BusinessRatingRead](
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

    async def read_by_id(self, id: str) -> BaseResponse[BusinessRatingRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_business_rating_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Rating not found")
        return BaseResponse[BusinessRatingRead](
            status_code=200, message="Successful", data=_to_read(row)
        )

    async def read_by_business_id(self, business_id: str) -> BaseResponse[list[BusinessRatingRead]]:
        rows = await self._repo.read_by_business_id(_parse_id(business_id))
        return BaseResponse[list[BusinessRatingRead]](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
        )


from app.utility.service_deps import readable_service, writable_service

WritableBusinessRatingService = writable_service(BusinessRatingService)
ReadableBusinessRatingService = readable_service(BusinessRatingService)
