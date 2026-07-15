from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.author.repository import AuthorRepository
from app.book.repository import BookRepository
from app.book_author.repository import BookAuthorRepository
from app.business.repository import BusinessRepository
from app.business_book.model import (
    SELLER_LISTING_STATUS_TRANSITIONS,
    SELLER_MUTABLE_LISTING_STATUSES,
    BusinessBookCreateRequest,
    BusinessBookUpdateRequest,
    BusinessBookWithVariants,
    BusinessBookWithVariantSummary,
    PublicCatalogBusinessBookDetail,
    PublicCatalogBusinessBookRead,
)
from app.business_book.repository import BusinessBookRepository
from app.business_book.schemas import BusinessBookCreate, BusinessBookRead, BusinessBookUpdate
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service
from app.variant.model import VariantWithConfig
from app.variant.repository import VariantRepository, effective_price
from app.variant.schemas import PublicCatalogVariantRead, VariantRead, VariantWithConfigRead


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
        self._repo = BusinessBookRepository(session)
        self._variant_repo = VariantRepository(session)
        self._book_repo = BookRepository(session)
        self._business_repo = BusinessRepository(session)
        self._book_author_repo = BookAuthorRepository(session)
        self._author_repo = AuthorRepository(session)

    async def create(self, item: BusinessBookCreateRequest, business_id: str) -> Response:
        await self._repo.create_business_book(_to_create(item, business_id))
        return Response(status_code=201)

    async def update(
        self,
        id: str,
        item: BusinessBookUpdateRequest,
        business_id: str,
    ) -> Response:
        existing = await self._repo.read_business_book_by_id(_parse_id(id))
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
            and item.status
            not in SELLER_LISTING_STATUS_TRANSITIONS.get(existing.status, frozenset())
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change listing status from {existing.status} to {item.status}",
            )

        updated = await self._repo.update_business_book(_parse_id(id), _to_update(item))
        if updated is None:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        return Response(status_code=200)

    async def delete(self, id: str, business_id: str) -> Response:
        existing = await self._repo.read_business_book_by_id(_parse_id(id))
        if existing is None:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        if str(existing.business_id) != business_id:
            raise HTTPException(status_code=403, detail="Cannot delete another business's listing")

        await self._variant_repo.soft_delete_variants_by_business_book(_parse_id(id))
        deleted = await self._repo.soft_delete_business_book(_parse_id(id))
        if not deleted:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[BusinessBookRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_business_books()
        rows = await self._repo.list_business_books(offset=offset, limit=size)

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

        total_results = await self._repo.count_business_books(business_id=parsed_business_id)
        rows = await self._repo.list_business_books(
            offset=offset,
            limit=size,
            business_id=parsed_business_id,
        )
        bb_ids = [row.id for row in rows]
        summaries = await self._variant_repo.variant_summary_for_business_books(bb_ids)
        books = await self._book_repo.read_books_by_ids([row.book_id for row in rows])
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
        row = await self._repo.read_business_book_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        if business_id and str(row.business_id) != business_id:
            raise HTTPException(status_code=403, detail="Not your business listing")

        book = await self._book_repo.read_book_by_id(row.book_id)
        variant_rows = await self._variant_repo.list_variants(
            offset=0,
            limit=100,
            business_book_id=parsed_id,
        )
        config_map = await self._variant_repo.resolve_configs_for_variants(
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

    async def _author_names_by_book_id(self, book_ids: list[uuid.UUID]) -> dict[str, list[str]]:
        if not book_ids:
            return {}
        links = await self._book_author_repo.read_by_book_ids(book_ids)
        author_ids = list({link.author_id for link in links})
        authors = await self._author_repo.read_authors_by_ids(author_ids)
        author_by_id = {
            str(row.id): f"{row.first_name} {row.last_name}".strip() or "Unknown"
            for row in authors
        }
        names_by_book: dict[str, list[str]] = {}
        for link in links:
            bid = str(link.book_id)
            name = author_by_id.get(str(link.author_id))
            if name:
                names_by_book.setdefault(bid, []).append(name)
        return names_by_book

    async def _to_public_catalog_reads(
        self, rows: list
    ) -> list[PublicCatalogBusinessBookRead]:
        if not rows:
            return []
        bb_ids = [row.id for row in rows]
        summaries = await self._variant_repo.variant_summary_for_business_books(
            bb_ids, purchasable_only=True
        )
        books = await self._book_repo.read_books_by_ids([row.book_id for row in rows])
        book_by_id = {book.id: book for book in books}
        author_names = await self._author_names_by_book_id([row.book_id for row in rows])

        data: list[PublicCatalogBusinessBookRead] = []
        for row in rows:
            summary = summaries.get(str(row.id), {})
            variant_count = int(summary.get("variant_count") or 0)
            if variant_count <= 0:
                continue
            book = book_by_id.get(row.book_id)
            if book is None:
                continue
            business = await self._business_repo.read_by_id(row.business_id)
            if business is None:
                continue
            data.append(
                PublicCatalogBusinessBookRead(
                    id=str(row.id),
                    book_id=str(row.book_id),
                    business_id=str(row.business_id),
                    business_name=business.name,
                    book_title=book.title,
                    book_image=row.image or book.image,
                    synopsis=row.synopsis or book.synopsis,
                    image=row.image,
                    author_names=author_names.get(str(row.book_id), []),
                    variant_count=variant_count,
                    min_price=summary.get("min_price"),
                )
            )
        return data

    async def _public_variants_for_listing(
        self, row, book, business
    ) -> list[PublicCatalogVariantRead]:
        variant_rows = await self._variant_repo.list_variants(
            offset=0,
            limit=100,
            business_book_id=row.id,
            active_catalog_only=True,
        )
        if not variant_rows:
            return []
        config_map = await self._variant_repo.resolve_configs_for_variants(
            [variant.id for variant in variant_rows]
        )
        items: list[PublicCatalogVariantRead] = []
        for variant_row in variant_rows:
            items.append(
                PublicCatalogVariantRead(
                    id=str(variant_row.id),
                    business_book_id=str(row.id),
                    book_id=str(book.id),
                    book_title=book.title,
                    book_image=variant_row.image or row.image or book.image,
                    business_id=str(business.id),
                    business_name=business.name,
                    price=effective_price(variant_row.price, variant_row.discount),
                    currency=variant_row.currency,
                    discount=(
                        float(variant_row.discount)
                        if variant_row.discount is not None
                        else None
                    ),
                    stock=variant_row.stock,
                    image=variant_row.image,
                    config=config_map.get(variant_row.id, []),
                )
            )
        return items

    async def read_public_catalog(
        self,
        params: ParamRequest,
        *,
        book_id: str | None = None,
        exclude_id: str | None = None,
    ) -> PaginatedResponse[PublicCatalogBusinessBookRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        parsed_book_id = _parse_id(book_id) if book_id else None
        parsed_exclude_id = _parse_id(exclude_id) if exclude_id else None
        search = (params.search or "").strip() or None

        total_results = await self._repo.count_public_catalog(
            book_id=parsed_book_id,
            exclude_id=parsed_exclude_id,
            search=search,
        )
        rows = await self._repo.list_public_catalog(
            offset=offset,
            limit=size,
            book_id=parsed_book_id,
            exclude_id=parsed_exclude_id,
            search=search,
        )
        data = await self._to_public_catalog_reads(rows)

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[PublicCatalogBusinessBookRead](
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

    async def read_public_by_id(self, id: str) -> BaseResponse[PublicCatalogBusinessBookDetail]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_business_book_by_id(parsed_id)
        if row is None or row.status != "ACTIVE":
            raise HTTPException(status_code=404, detail="Listing not found")

        book = await self._book_repo.read_book_by_id(row.book_id)
        if book is None:
            raise HTTPException(status_code=404, detail="Listing not found")
        business = await self._business_repo.read_by_id(row.business_id)
        if business is None:
            raise HTTPException(status_code=404, detail="Listing not found")

        variants = await self._public_variants_for_listing(row, book, business)
        if not variants:
            raise HTTPException(status_code=404, detail="Listing not found")

        author_names = await self._author_names_by_book_id([row.book_id])
        summary = await self._variant_repo.variant_summary_for_business_books(
            [row.id], purchasable_only=True
        )
        listing_summary = summary.get(str(row.id), {})

        return BaseResponse[PublicCatalogBusinessBookDetail](
            status_code=200,
            message="Successful",
            data=PublicCatalogBusinessBookDetail(
                id=str(row.id),
                book_id=str(row.book_id),
                business_id=str(row.business_id),
                business_name=business.name,
                book_title=book.title,
                book_image=row.image or book.image,
                synopsis=row.synopsis or book.synopsis,
                image=row.image,
                author_names=author_names.get(str(row.book_id), []),
                variant_count=int(listing_summary.get("variant_count") or 0),
                min_price=listing_summary.get("min_price"),
                variants=variants,
            ),
        )


class WritableBusinessBookService(writable_service(BusinessBookService)):
    pass


class ReadableBusinessBookService(readable_service(BusinessBookService)):
    pass
