from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from app.book.repository import read_book_by_id, read_books_by_ids
from app.business_book.model import (
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithVariantSummary,
    BusinessBookWithVariants,
)
from app.business_book.repository import (
    create_business_book,
    list_business_books,
    read_business_book_by_id,
    soft_delete_business_book,
    update_business_book,
    count_business_books,
)
from app.business_book.schemas import BusinessBookCreate, BusinessBookRead, BusinessBookUpdate
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker
from app.variant.model import VariantWithConfig
from app.variant.schemas import VariantRead, VariantWithConfigRead
from app.variant.repository import (
    list_variants,
    resolve_configs_for_variants,
    soft_delete_variants_by_business_book,
    variant_summary_for_business_books,
)


@dataclass
class UpdateResult:
    matched_count: int


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


async def create_query(item: BusinessBookCreateRequest, business_id: str) -> None:
    async with get_sessionmaker()() as session:
        await create_business_book(session, _to_create(item, business_id))
        await session.commit()


async def update_query(id: str, item: BusinessBookUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        updated = await update_business_book(session, parsed_id, _to_update(item))
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        await soft_delete_variants_by_business_book(session, parsed_id)
        deleted = await soft_delete_business_book(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def read_query(params: ParamRequest) -> PaginatedData[BusinessBookRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_business_books(session)
        rows = await list_business_books(session, offset=offset, limit=size)

    total_pages = math.ceil(total_results / size) if size else 1
    return PaginatedData(
        data=[_to_read(row) for row in rows],
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_business_id_query(
    business_id: str,
    params: ParamRequest,
) -> PaginatedData[BusinessBookWithVariantSummary]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size
    parsed_business_id = _parse_id(business_id)

    async with get_sessionmaker()() as session:
        total_results = await count_business_books(session, business_id=parsed_business_id)
        rows = await list_business_books(
            session,
            offset=offset,
            limit=size,
            business_id=parsed_business_id,
        )
        bb_ids = [row.id for row in rows]
        summaries = await variant_summary_for_business_books(session, bb_ids)
        books = await read_books_by_ids(session, [row.book_id for row in rows])
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
    return PaginatedData(
        data=data,
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_id_query(id: str) -> BusinessBookRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_business_book_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_id_with_variants_query(id: str) -> BusinessBookWithVariants | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_business_book_by_id(session, parsed_id)
        if row is None:
            return None
        book = await read_book_by_id(session, row.book_id)
        variant_rows = await list_variants(
            session,
            offset=0,
            limit=100,
            business_book_id=parsed_id,
        )
        config_map = await resolve_configs_for_variants(session, [variant.id for variant in variant_rows])

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

        return BusinessBookWithVariants(
            **_to_read(row).model_dump(mode="json"),
            book_title=book.title if book else None,
            book_image=book.image if book else None,
            variants=variants,
        )
