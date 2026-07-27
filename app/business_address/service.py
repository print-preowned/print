from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_address.model import BusinessAddressCreateRequest, BusinessAddressUpdateRequest
from app.business_address.repository import BusinessAddressRepository
from app.business_address.schemas import (
    BusinessAddressCreate,
    BusinessAddressRead,
    BusinessAddressUpdate,
)
from app.utility.address import (
    MAX_BUSINESS_ADDRESSES,
    normalize_whitespace,
    validate_nigeria_address_fields,
)
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Location not found") from exc


def _parse_business_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BusinessAddressRead:
    return BusinessAddressRead.model_validate(row)


def _validated_create_fields(payload: BusinessAddressCreateRequest) -> dict[str, str | None | bool]:
    label = normalize_whitespace(payload.label)
    if not label:
        raise HTTPException(status_code=422, detail="Location label is required")

    address_fields = validate_nigeria_address_fields(
        line1=payload.line1,
        line2=payload.line2,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        country_code=payload.country_code,
        phone_number=payload.phone_number,
        require_phone=False,
    )
    return {
        "label": label,
        **address_fields,
        "is_primary": payload.is_primary,
        "pickup_enabled": payload.pickup_enabled,
    }


class BusinessAddressService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BusinessAddressRepository(session)

    async def create(
        self,
        payload: BusinessAddressCreateRequest,
        business_id: str,
    ) -> BaseResponse[BusinessAddressRead]:
        parsed_business_id = _parse_business_id(business_id)
        active_count = await self._repo.count_active_by_business(parsed_business_id)
        if active_count >= MAX_BUSINESS_ADDRESSES:
            raise HTTPException(status_code=422, detail="Maximum number of store locations reached")

        fields = _validated_create_fields(payload)
        is_primary = bool(fields.pop("is_primary")) or active_count == 0

        if is_primary:
            await self._repo.clear_primary_for_business(parsed_business_id)

        if fields.get("pickup_enabled"):
            await self._repo.clear_pickup_enabled_for_business(parsed_business_id)

        row = await self._repo.create(
            BusinessAddressCreate(
                business_id=parsed_business_id,
                is_primary=is_primary,
                **fields,  # type: ignore[arg-type]
            )
        )
        return BaseResponse[BusinessAddressRead](
            status_code=201,
            message="Successful",
            data=_to_read(row),
        )

    async def update(
        self,
        address_id: str,
        payload: BusinessAddressUpdateRequest,
        business_id: str,
    ) -> BaseResponse[BusinessAddressRead]:
        parsed_id = _parse_id(address_id)
        parsed_business_id = _parse_business_id(business_id)
        row = await self._repo.read_by_id(parsed_id, parsed_business_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Location not found")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return BaseResponse[BusinessAddressRead](
                status_code=200,
                message="Successful",
                data=_to_read(row),
            )

        merged = {
            "line1": update_data.get("line1", row.line1),
            "line2": update_data.get("line2", row.line2),
            "city": update_data.get("city", row.city),
            "state": update_data.get("state", row.state),
            "postal_code": update_data.get("postal_code", row.postal_code),
            "country_code": update_data.get("country_code", row.country_code),
            "phone_number": update_data.get("phone_number", row.phone_number),
        }
        if any(k in update_data for k in merged):
            validated = validate_nigeria_address_fields(**merged, require_phone=False)
            update_data.update(validated)

        if "label" in update_data:
            label = normalize_whitespace(update_data["label"])
            if not label:
                raise HTTPException(status_code=422, detail="Location label is required")
            update_data["label"] = label

        if update_data.get("is_primary") is True:
            await self._repo.clear_primary_for_business(parsed_business_id, exclude_id=parsed_id)

        if update_data.get("pickup_enabled") is True:
            await self._repo.clear_pickup_enabled_for_business(
                parsed_business_id,
                exclude_id=parsed_id,
            )

        updated = await self._repo.update(
            parsed_id,
            parsed_business_id,
            BusinessAddressUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Location not found")
        return BaseResponse[BusinessAddressRead](
            status_code=200,
            message="Successful",
            data=_to_read(updated),
        )

    async def delete(self, address_id: str, business_id: str) -> Response:
        parsed_id = _parse_id(address_id)
        parsed_business_id = _parse_business_id(business_id)
        row = await self._repo.read_by_id(parsed_id, parsed_business_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Location not found")

        active_count = await self._repo.count_active_by_business(parsed_business_id)
        if active_count <= 1:
            raise HTTPException(status_code=422, detail="Cannot delete your only store location")

        was_primary = row.is_primary
        deleted = await self._repo.delete(parsed_id, parsed_business_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Location not found")

        if was_primary:
            replacement = await self._repo.find_first_active_for_business(parsed_business_id)
            if replacement is not None:
                await self._repo.set_primary(replacement.id, parsed_business_id)

        return Response(status_code=204)

    async def set_primary(self, address_id: str, business_id: str) -> Response:
        parsed_id = _parse_id(address_id)
        parsed_business_id = _parse_business_id(business_id)
        row = await self._repo.set_primary(parsed_id, parsed_business_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Location not found")
        return Response(status_code=204)

    async def read(
        self,
        business_id: str,
        params: ParamRequest,
    ) -> PaginatedResponse[BusinessAddressRead]:
        parsed_business_id = _parse_business_id(business_id)
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_active_by_business(parsed_business_id)
        rows = await self._repo.list_by_business(parsed_business_id, offset=offset, limit=size)
        total_pages = math.ceil(total_results / size) if size else 1

        return PaginatedResponse[BusinessAddressRead](
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

    async def read_by_id(self, address_id: str, business_id: str) -> BaseResponse[BusinessAddressRead]:
        parsed_id = _parse_id(address_id)
        parsed_business_id = _parse_business_id(business_id)
        row = await self._repo.read_by_id(parsed_id, parsed_business_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Location not found")
        return BaseResponse[BusinessAddressRead](
            status_code=200,
            message="Successful",
            data=_to_read(row),
        )

    async def read_pickup_location_for_customer(
        self,
        business_id: str,
    ) -> BaseResponse[BusinessAddressRead]:
        try:
            parsed_business_id = _parse_business_id(business_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Pickup location not found") from exc
        row = await self._repo.read_pickup_location_by_business(parsed_business_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Pickup location not found")
        return BaseResponse[BusinessAddressRead](
            status_code=200,
            message="Successful",
            data=_to_read(row),
        )


class WritableBusinessAddressService(writable_service(BusinessAddressService)):
    pass


class ReadableBusinessAddressService(readable_service(BusinessAddressService)):
    pass
