from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException

from app.book.repository import read_books_by_ids
from app.business.repository import read_business_by_id
from app.business_book.repository import read_business_books_by_ids
from app.utility.model import PaginatedData, Pagination, ParamRequest
from app.utility.postgres import get_sessionmaker
from app.variant.model import VariantCreateRequest, VariantUpdateRequest
from app.variant.repository import (
    create_variant,
    duplicate_option_set_exists,
    effective_price,
    list_variants,
    read_variant_by_id,
    resolve_configs_for_variants,
    soft_delete_variant,
    soft_delete_variants_by_business_book,
    update_variant,
    validate_product_option_values,
    count_variants,
    variant_summary_for_business_books,
)
from app.variant.schemas import (
    PublicCatalogVariantRead,
    ResolvedConfigRead,
    VariantCreate,
    VariantRead,
    VariantUpdate,
    VariantWithConfigRead,
)


@dataclass
class UpdateResult:
    matched_count: int


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> VariantRead:
    return VariantRead.model_validate(row)


def _to_variant_with_config(row, configs: list[ResolvedConfigRead]) -> VariantWithConfigRead:
    return VariantWithConfigRead(
        **_to_read(row).model_dump(),
        config=configs,
    )


async def update_query(id: str, item: VariantUpdateRequest) -> UpdateResult:
    parsed_id = _parse_id(id)
    data = item.model_dump(exclude_unset=True)
    if "price" in data and data["price"] is not None:
        data["price"] = Decimal(str(data["price"]))
    if "discount" in data and data["discount"] is not None:
        data["discount"] = Decimal(str(data["discount"]))
    async with get_sessionmaker()() as session:
        updated = await update_variant(
            session,
            parsed_id,
            VariantUpdate(**data),
        )
        if updated is None:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_query(id: str) -> UpdateResult:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        deleted = await soft_delete_variant(session, parsed_id)
        if not deleted:
            return UpdateResult(matched_count=0)
        await session.commit()
    return UpdateResult(matched_count=1)


async def delete_by_business_book_query(business_book_id: str) -> None:
    parsed_id = _parse_id(business_book_id)
    async with get_sessionmaker()() as session:
        await soft_delete_variants_by_business_book(session, parsed_id)
        await session.commit()


async def read_query(params: ParamRequest) -> PaginatedData[VariantRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_variants(session)
        rows = await list_variants(session, offset=offset, limit=size)

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


async def read_by_id_query(id: str) -> VariantRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_variant_by_id(session, parsed_id)
    return _to_read(row) if row else None


async def read_by_business_book_id_query(
    business_book_id: str,
    params: ParamRequest,
) -> PaginatedData[VariantWithConfigRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size
    parsed_bb_id = _parse_id(business_book_id)

    async with get_sessionmaker()() as session:
        total_results = await count_variants(session, business_book_id=parsed_bb_id)
        rows = await list_variants(
            session,
            offset=offset,
            limit=size,
            business_book_id=parsed_bb_id,
        )
        config_map = await resolve_configs_for_variants(session, [row.id for row in rows])

    total_pages = math.ceil(total_results / size) if size else 1
    return PaginatedData(
        data=[
            _to_variant_with_config(row, config_map.get(row.id, []))
            for row in rows
        ],
        pagination=Pagination(
            page=page,
            size=size,
            total_pages=total_pages,
            total_results=total_results,
        ),
    )


async def read_by_id_with_config_query(id: str) -> VariantWithConfigRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_variant_by_id(session, parsed_id)
        if row is None:
            return None
        config_map = await resolve_configs_for_variants(session, [row.id])
    return _to_variant_with_config(row, config_map.get(row.id, []))


async def create_query(business_book_id: str, payload: VariantCreateRequest) -> str:
    parsed_bb_id = _parse_id(business_book_id)
    value_ids = [uuid.UUID(str(option_id)) for option_id in payload.variant_option_ids]

    async with get_sessionmaker()() as session:
        try:
            await validate_product_option_values(session, value_ids)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if await duplicate_option_set_exists(session, parsed_bb_id, value_ids):
            raise HTTPException(
                status_code=409,
                detail="A variant with this option combination already exists",
            )

        fields = payload.model_dump(exclude={"variant_option_ids"})
        created = await create_variant(
            session,
            VariantCreate(
                business_book_id=parsed_bb_id,
                description=fields.get("description"),
                stock=fields["stock"],
                price=Decimal(str(fields["price"])),
                currency=fields.get("currency") or "USD",
                discount=Decimal(str(fields["discount"])) if fields.get("discount") is not None else None,
                sku=fields.get("sku"),
                image=fields.get("image"),
                product_option_value_ids=value_ids,
            ),
        )
        await session.commit()
        return str(created.id)


async def read_public_catalog_query(
    params: ParamRequest,
) -> PaginatedData[PublicCatalogVariantRead]:
    page = max(1, params.page)
    size = params.size
    offset = (page - 1) * size

    async with get_sessionmaker()() as session:
        total_results = await count_variants(session, active_catalog_only=True)
        rows = await list_variants(
            session,
            offset=offset,
            limit=size,
            active_catalog_only=True,
        )
        if not rows:
            total_pages = math.ceil(total_results / size) if size else 1
            return PaginatedData(
                data=[],
                pagination=Pagination(
                    page=page,
                    size=size,
                    total_pages=total_pages,
                    total_results=total_results,
                ),
            )

        bb_ids = [row.business_book_id for row in rows]
        business_books = await read_business_books_by_ids(session, bb_ids)
        bb_by_id = {row.id: row for row in business_books}

        books = await read_books_by_ids(session, [bb.book_id for bb in business_books])
        book_by_id = {row.id: row for row in books}

        config_map = await resolve_configs_for_variants(session, [row.id for row in rows])

        data: list[PublicCatalogVariantRead] = []
        for row in rows:
            bb = bb_by_id.get(row.business_book_id)
            if bb is None or bb.status != "ACTIVE":
                continue
            book = book_by_id.get(bb.book_id)
            if book is None:
                continue
            business = await read_business_by_id(session, bb.business_id)
            if business is None:
                continue
            data.append(
                PublicCatalogVariantRead(
                    id=str(row.id),
                    business_book_id=str(bb.id),
                    book_id=str(book.id),
                    book_title=book.title,
                    book_image=row.image or bb.image or book.image,
                    business_id=str(business.id),
                    business_name=business.name,
                    price=effective_price(row.price, row.discount),
                    currency=row.currency,
                    discount=float(row.discount) if row.discount is not None else None,
                    stock=row.stock,
                    image=row.image,
                    config=config_map.get(row.id, []),
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


async def read_public_catalog_by_id_query(id: str) -> PublicCatalogVariantRead | None:
    parsed_id = _parse_id(id)
    async with get_sessionmaker()() as session:
        row = await read_variant_by_id(session, parsed_id)
        if row is None or row.status != "ACTIVE" or row.stock <= 0:
            return None
        bb_list = await read_business_books_by_ids(session, [row.business_book_id])
        if not bb_list or bb_list[0].status != "ACTIVE":
            return None
        bb = bb_list[0]
        books = await read_books_by_ids(session, [bb.book_id])
        if not books:
            return None
        book = books[0]
        business = await read_business_by_id(session, bb.business_id)
        if business is None:
            return None
        config_map = await resolve_configs_for_variants(session, [row.id])

    return PublicCatalogVariantRead(
        id=str(row.id),
        business_book_id=str(bb.id),
        book_id=str(book.id),
        book_title=book.title,
        book_image=row.image or bb.image or book.image,
        business_id=str(business.id),
        business_name=business.name,
        price=effective_price(row.price, row.discount),
        currency=row.currency,
        discount=float(row.discount) if row.discount is not None else None,
        stock=row.stock,
        image=row.image,
        config=config_map.get(row.id, []),
    )
