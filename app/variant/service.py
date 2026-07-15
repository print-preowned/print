from __future__ import annotations

import math
import uuid
from decimal import Decimal

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.book.repository import BookRepository
from app.business.repository import BusinessRepository
from app.business_book.repository import BusinessBookRepository
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service
from app.variant.model import VariantCreateRequest, VariantUpdateRequest
from app.variant.repository import VariantRepository, effective_price
from app.variant.schemas import (
    PublicCatalogVariantRead,
    ResolvedConfigRead,
    VariantCreate,
    VariantRead,
    VariantUpdate,
    VariantWithConfigRead,
)


def _parse_id(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def _to_read(row) -> VariantRead:
    return VariantRead.model_validate(row)


def _to_variant_with_config(row, configs: list[ResolvedConfigRead]) -> VariantWithConfigRead:
    return VariantWithConfigRead(
        **_to_read(row).model_dump(),
        config=configs,
    )


class VariantService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = VariantRepository(session)
        self._book_repo = BookRepository(session)
        self._business_repo = BusinessRepository(session)
        self._business_book_repo = BusinessBookRepository(session)

    async def _assert_business_book_owned(self, business_book_id: str, business_id: str):
        bb = await self._business_book_repo.read_business_book_by_id(_parse_id(business_book_id))
        if bb is None:
            raise HTTPException(status_code=404, detail="BusinessBook not found")
        if str(bb.business_id) != business_id:
            raise HTTPException(status_code=403, detail="Not your business listing")
        return bb

    async def _assert_variant_belongs_to_business_book(
        self,
        variant_id: str,
        business_book_id: str,
        business_id: str,
    ):
        await self._assert_business_book_owned(business_book_id, business_id)
        variant = await self._repo.read_variant_by_id(_parse_id(variant_id))
        if variant is None:
            raise HTTPException(status_code=404, detail="Variant not found")
        if str(variant.business_book_id) != business_book_id:
            raise HTTPException(status_code=403, detail="Variant does not belong to this listing")
        return variant

    async def create(
        self,
        business_book_id: str,
        payload: VariantCreateRequest,
        business_id: str,
    ) -> BaseResponse[dict]:
        await self._assert_business_book_owned(business_book_id, business_id)
        parsed_bb_id = _parse_id(business_book_id)
        value_ids = [uuid.UUID(str(option_id)) for option_id in payload.variant_option_ids]

        try:
            await self._repo.validate_product_option_values(value_ids)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if await self._repo.duplicate_option_set_exists(parsed_bb_id, value_ids):
            raise HTTPException(
                status_code=409,
                detail="A variant with this option combination already exists",
            )

        fields = payload.model_dump(exclude={"variant_option_ids"})
        created = await self._repo.create_variant(
            VariantCreate(
                business_book_id=parsed_bb_id,
                description=fields.get("description"),
                stock=fields["stock"],
                price=Decimal(str(fields["price"])),
                currency=fields.get("currency") or "USD",
                discount=Decimal(str(fields["discount"]))
                if fields.get("discount") is not None
                else None,
                sku=fields.get("sku"),
                image=fields.get("image"),
                product_option_value_ids=value_ids,
            ),
        )
        variant_id = str(created.id)
        return BaseResponse(status_code=201, message="Created", data={"id": variant_id})

    async def update(
        self,
        business_book_id: str,
        variant_id: str,
        payload: VariantUpdateRequest,
        business_id: str,
    ) -> Response:
        await self._assert_variant_belongs_to_business_book(
            variant_id, business_book_id, business_id
        )
        data = payload.model_dump(exclude_unset=True)
        if "price" in data and data["price"] is not None:
            data["price"] = Decimal(str(data["price"]))
        if "discount" in data and data["discount"] is not None:
            data["discount"] = Decimal(str(data["discount"]))
        update = await self._repo.update_variant(_parse_id(variant_id), VariantUpdate(**data))
        if update is None:
            raise HTTPException(status_code=404, detail="Variant not found")
        return Response(status_code=200)

    async def delete(
        self,
        business_book_id: str,
        variant_id: str,
        business_id: str,
    ) -> Response:
        await self._assert_variant_belongs_to_business_book(
            variant_id, business_book_id, business_id
        )
        deleted = await self._repo.soft_delete_variant(_parse_id(variant_id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Variant not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[VariantRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        total_results = await self._repo.count_variants()
        rows = await self._repo.list_variants(offset=offset, limit=size)
        return PaginatedResponse[VariantRead](
            status_code=200,
            message="Successful",
            data=[_to_read(row) for row in rows],
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=math.ceil(total_results / size) if size else 1,
                total_results=total_results,
            ),
        )

    async def read_scoped(
        self,
        business_book_id: str,
        params: ParamRequest,
        business_id: str,
    ) -> PaginatedResponse[VariantWithConfigRead]:
        await self._assert_business_book_owned(business_book_id, business_id)
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        parsed_bb_id = _parse_id(business_book_id)
        total_results = await self._repo.count_variants(business_book_id=parsed_bb_id)
        rows = await self._repo.list_variants(
            offset=offset,
            limit=size,
            business_book_id=parsed_bb_id,
        )
        config_map = await self._repo.resolve_configs_for_variants([row.id for row in rows])
        return PaginatedResponse[VariantWithConfigRead](
            status_code=200,
            message="Successful",
            data=[_to_variant_with_config(row, config_map.get(row.id, [])) for row in rows],
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=math.ceil(total_results / size) if size else 1,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str) -> BaseResponse[VariantRead]:
        row = await self._repo.read_variant_by_id(_parse_id(id))
        if row is None:
            raise HTTPException(status_code=404, detail="Variant not found")
        return BaseResponse[VariantRead](status_code=200, message="Successful", data=_to_read(row))

    async def read_by_id_with_config(self, id: str) -> BaseResponse[VariantWithConfigRead]:
        row = await self._repo.read_variant_by_id(_parse_id(id))
        if row is None:
            raise HTTPException(status_code=404, detail="Variant not found")
        config_map = await self._repo.resolve_configs_for_variants([row.id])
        return BaseResponse[VariantWithConfigRead](
            status_code=200,
            message="Successful",
            data=_to_variant_with_config(row, config_map.get(row.id, [])),
        )

    async def read_public_catalog(
        self,
        params: ParamRequest,
        book_id: str | None = None,
    ) -> PaginatedResponse[PublicCatalogVariantRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        parsed_book_id = _parse_id(book_id) if book_id else None

        total_results = await self._repo.count_variants(
            active_catalog_only=True,
            book_id=parsed_book_id,
        )
        rows = await self._repo.list_variants(
            offset=offset,
            limit=size,
            active_catalog_only=True,
            book_id=parsed_book_id,
        )
        data: list[PublicCatalogVariantRead] = []
        if rows:
            bb_ids = [row.business_book_id for row in rows]
            business_books = await self._business_book_repo.read_business_books_by_ids(bb_ids)
            bb_by_id = {row.id: row for row in business_books}

            books = await self._book_repo.read_books_by_ids([bb.book_id for bb in business_books])
            book_by_id = {row.id: row for row in books}

            config_map = await self._repo.resolve_configs_for_variants([row.id for row in rows])

            for row in rows:
                bb = bb_by_id.get(row.business_book_id)
                if bb is None or bb.status != "ACTIVE":
                    continue
                book = book_by_id.get(bb.book_id)
                if book is None:
                    continue
                business = await self._business_repo.read_by_id(bb.business_id)
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
        return PaginatedResponse[PublicCatalogVariantRead](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=math.ceil(total_results / size) if size else 1,
                total_results=total_results,
            ),
        )

    async def read_public_catalog_by_id(self, id: str) -> BaseResponse[PublicCatalogVariantRead]:
        row = await self._repo.read_variant_by_id(_parse_id(id))
        if row is None or row.status != "ACTIVE" or row.stock <= 0:
            raise HTTPException(status_code=404, detail="Variant not found")
        bb_list = await self._business_book_repo.read_business_books_by_ids([row.business_book_id])
        if not bb_list or bb_list[0].status != "ACTIVE":
            raise HTTPException(status_code=404, detail="Variant not found")
        bb = bb_list[0]
        books = await self._book_repo.read_books_by_ids([bb.book_id])
        if not books:
            raise HTTPException(status_code=404, detail="Variant not found")
        book = books[0]
        business = await self._business_repo.read_by_id(bb.business_id)
        if business is None:
            raise HTTPException(status_code=404, detail="Variant not found")
        config_map = await self._repo.resolve_configs_for_variants([row.id])
        item = PublicCatalogVariantRead(
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
        return BaseResponse[PublicCatalogVariantRead](
            status_code=200, message="Successful", data=item
        )


class WritableVariantService(writable_service(VariantService)):
    pass


class ReadableVariantService(readable_service(VariantService)):
    pass
