from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.book.repository import read_book_by_id, read_books_by_ids
from app.business_book.model import (
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithVariantSummary,
    BusinessBookWithVariants,
    SELLER_LISTING_STATUS_TRANSITIONS,
    SELLER_MUTABLE_LISTING_STATUSES,
)
from app.business_book.repository import (
    count_business_books,
    create_business_book,
    list_business_books,
    read_business_book_by_id,
    soft_delete_business_book,
    update_business_book,
)
from app.business_book.schemas import BusinessBookCreate, BusinessBookRead, BusinessBookUpdate
from app.utility.model import BaseResponse, PaginatedResponse, ParamRequest, Pagination
from app.utility.service_deps import readable_service, writable_service
from app.variant.model import VariantWithConfig
from app.variant.repository import (
    list_variants,
    resolve_configs_for_variants,
    soft_delete_variants_by_business_book,
    variant_summary_for_business_books,
)
from app.variant.schemas import VariantRead, VariantWithConfigRead


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> BusinessBookRead:
    return BusinessBookRead.model_validate(row)


def _to_create(item: BusinessBookCreateRequest, business_id: str) -> BusinessBookCreate:
    return BusinessBookCreate(
        book_id=uuid.UUID(str(item.book_id)),
        business_id=uuid.UUID(business_id),
        synopsis=item.synopsis,
        image=item.image,
        status="DRAFT",
    )


def _to_update(item: BusinessBookUpdateRequest) -> BusinessBookUpdate:
    data = item.model_dump(exclude_unset=True, exclude={"business_id"})
    if "book_id" in data and data["book_id"] is not None:
        data["book_id"] = uuid.UUID(str(data["book_id"]))
    return BusinessBookUpdate(**data)


class BusinessBookService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item: BusinessBookCreateRequest, business_id: str) -> Response:
        await create_business_book(self._session, _to_create(item, business_id))
        return Response(status_code=201)

    async def update(
        self,
        id: str,
        item: BusinessBookUpdateRequest,
        business_id: str,
    ) -> Response:
        existing = await read_business_book_by_id(self._session, _parse_id(id))
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
            and item.status not in SELLER_LISTING_STATUS_TRANSITIONS.get(existing.status, frozenset())
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change listing status from {existing.status} to {item.status}",
            )

        updated = await update_business_book(self._session, _parse_id(id), _to_update(item))
        if updated is None:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        return Response(status_code=200)

    async def delete(self, id: str, business_id: str) -> Response:
        existing = await read_business_book_by_id(self._session, _parse_id(id))
        if existing is None:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        if str(existing.business_id) != business_id:
            raise HTTPException(status_code=403, detail="Cannot delete another business's listing")

        await soft_delete_variants_by_business_book(self._session, _parse_id(id))
        deleted = await soft_delete_business_book(self._session, _parse_id(id))
        if not deleted:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BusinessBookRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await count_business_books(self._session)
        rows = await list_business_books(self._session, offset=offset, limit=size)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[BusinessBookRead](
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

    async def read_by_business_id(
        self,
        business_id: str,
        params: ParamRequest,
    ) -> PaginatedResponse[BusinessBookWithVariantSummary]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        parsed_business_id = _parse_id(business_id)

        total_results = await count_business_books(self._session, business_id=parsed_business_id)
        rows = await list_business_books(
            self._session,
            offset=offset,
            limit=size,
            business_id=parsed_business_id,
        )
        bb_ids = [row.id for row in rows]
        summaries = await variant_summary_for_business_books(self._session, bb_ids)
        books = await read_books_by_ids(self._session, [row.book_id for row in rows])
        book_by_id = {book.id: book for book in books}

        data: list[BusinessBookWithVariantSummary] = []
        for row in rows:
            book = book_by_id.get(row.book_id)
            summary = summaries.get(str(row.id), {})
            data.append(
                BusinessBookWithVariantSummary(
                    **_to_read(row).model_dump(mode="json"),
                    book_title=book.title if book else None,
                    book_image=book.image if book else None,
                    variant_count=int(summary.get("variant_count") or 0),
                    min_price=summary.get("min_price"),
                    total_stock=int(summary.get("total_stock") or 0),
                )
            )

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[BusinessBookWithVariantSummary](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(
        self,
        id: str,
        business_id: str | None = None,
    ) -> BaseResponse[BusinessBookWithVariants]:
        parsed_id = _parse_id(id)
        row = await read_business_book_by_id(self._session, parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        if business_id and str(row.business_id) != business_id:
            raise HTTPException(status_code=403, detail="Not your business listing")

        book = await read_book_by_id(self._session, row.book_id)
        variant_rows = await list_variants(
            self._session,
            offset=0,
            limit=100,
            business_book_id=parsed_id,
        )
        config_map = await resolve_configs_for_variants(
            self._session,
            [variant.id for variant in variant_rows],
        )

        variants: list[VariantWithConfig] = []
        for variant_row in variant_rows:
            variant_read = VariantWithConfigRead(
                **VariantRead.model_validate(variant_row).model_dump(),
                config=config_map.get(variant_row.id, []),
            )
            variants.append(
                VariantWithConfig.model_validate(
                    {
                        **variant_read.model_dump(mode="json"),
                        "id": str(variant_read.id),
                        "business_book_id": str(variant_read.business_book_id),
                        "price": float(variant_read.price),
                        "discount": (
                            float(variant_read.discount)
                            if variant_read.discount is not None
                            else None
                        ),
                        "config": [config.model_dump() for config in variant_read.config],
                    }
                )
            )

        return BaseResponse[BusinessBookWithVariants](
            status_code=200,
            message="Successful",
            data=BusinessBookWithVariants(
                **_to_read(row).model_dump(mode="json"),
                book_title=book.title if book else None,
                book_image=book.image if book else None,
                variants=variants,
            ),
        )


class WritableBusinessBookService(writable_service(BusinessBookService)):
    pass


class ReadableBusinessBookService(readable_service(BusinessBookService)):
    pass
