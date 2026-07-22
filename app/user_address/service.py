from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.user_address.model import UserAddressCreateRequest, UserAddressUpdateRequest
from app.user_address.repository import UserAddressRepository
from app.user_address.schemas import UserAddressCreate, UserAddressRead, UserAddressUpdate
from app.utility.address import (
    MAX_USER_ADDRESSES,
    normalize_whitespace,
    validate_nigeria_address_fields,
)
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service


def _parse_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Address not found") from exc


def _parse_user_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> UserAddressRead:
    return UserAddressRead.model_validate(row)


def _validated_create_fields(payload: UserAddressCreateRequest) -> dict[str, str | None | bool]:
    recipient_name = normalize_whitespace(payload.recipient_name)
    if not recipient_name:
        raise HTTPException(status_code=422, detail="Recipient name is required")

    address_fields = validate_nigeria_address_fields(
        line1=payload.line1,
        line2=payload.line2,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        country_code=payload.country_code,
        phone_number=payload.phone_number,
        require_phone=True,
    )
    return {
        "label": normalize_whitespace(payload.label),
        "recipient_name": recipient_name,
        **address_fields,
        "is_default": payload.is_default,
    }


class UserAddressService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserAddressRepository(session)

    async def create(self, payload: UserAddressCreateRequest, user_id: str) -> BaseResponse[UserAddressRead]:
        parsed_user_id = _parse_user_id(user_id)
        active_count = await self._repo.count_active_by_user(parsed_user_id)
        if active_count >= MAX_USER_ADDRESSES:
            raise HTTPException(status_code=422, detail="Maximum number of saved addresses reached")

        fields = _validated_create_fields(payload)
        is_default = bool(fields.pop("is_default")) or active_count == 0

        if is_default:
            await self._repo.clear_default_for_user(parsed_user_id)

        row = await self._repo.create(
            UserAddressCreate(
                user_id=parsed_user_id,
                is_default=is_default,
                **fields,  # type: ignore[arg-type]
            )
        )
        return BaseResponse[UserAddressRead](
            status_code=201,
            message="Successful",
            data=_to_read(row),
        )

    async def update(
        self,
        address_id: str,
        payload: UserAddressUpdateRequest,
        user_id: str,
    ) -> BaseResponse[UserAddressRead]:
        parsed_id = _parse_id(address_id)
        parsed_user_id = _parse_user_id(user_id)
        row = await self._repo.read_by_id(parsed_id, parsed_user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Address not found")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return BaseResponse[UserAddressRead](
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
            validated = validate_nigeria_address_fields(**merged, require_phone=True)
            update_data.update(validated)

        if "recipient_name" in update_data:
            recipient_name = normalize_whitespace(update_data["recipient_name"])
            if not recipient_name:
                raise HTTPException(status_code=422, detail="Recipient name is required")
            update_data["recipient_name"] = recipient_name

        if "label" in update_data:
            update_data["label"] = normalize_whitespace(update_data["label"])

        if update_data.get("is_default") is True:
            await self._repo.clear_default_for_user(parsed_user_id, exclude_id=parsed_id)

        updated = await self._repo.update(
            parsed_id,
            parsed_user_id,
            UserAddressUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Address not found")
        return BaseResponse[UserAddressRead](
            status_code=200,
            message="Successful",
            data=_to_read(updated),
        )

    async def delete(self, address_id: str, user_id: str) -> Response:
        parsed_id = _parse_id(address_id)
        parsed_user_id = _parse_user_id(user_id)
        row = await self._repo.read_by_id(parsed_id, parsed_user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Address not found")

        active_count = await self._repo.count_active_by_user(parsed_user_id)
        if active_count <= 1:
            raise HTTPException(status_code=422, detail="Cannot delete your only saved address")

        was_default = row.is_default
        deleted = await self._repo.delete(parsed_id, parsed_user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Address not found")

        if was_default:
            replacement = await self._repo.find_first_active_for_user(parsed_user_id)
            if replacement is not None:
                await self._repo.set_default(replacement.id, parsed_user_id)

        return Response(status_code=204)

    async def set_default(self, address_id: str, user_id: str) -> Response:
        parsed_id = _parse_id(address_id)
        parsed_user_id = _parse_user_id(user_id)
        row = await self._repo.set_default(parsed_id, parsed_user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Address not found")
        return Response(status_code=204)

    async def read(self, user_id: str, params: ParamRequest) -> PaginatedResponse[UserAddressRead]:
        parsed_user_id = _parse_user_id(user_id)
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_active_by_user(parsed_user_id)
        rows = await self._repo.list_by_user(parsed_user_id, offset=offset, limit=size)
        total_pages = math.ceil(total_results / size) if size else 1

        return PaginatedResponse[UserAddressRead](
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

    async def read_by_id(self, address_id: str, user_id: str) -> BaseResponse[UserAddressRead]:
        parsed_id = _parse_id(address_id)
        parsed_user_id = _parse_user_id(user_id)
        row = await self._repo.read_by_id(parsed_id, parsed_user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Address not found")
        return BaseResponse[UserAddressRead](
            status_code=200,
            message="Successful",
            data=_to_read(row),
        )


class WritableUserAddressService(writable_service(UserAddressService)):
    pass


class ReadableUserAddressService(readable_service(UserAddressService)):
    pass
