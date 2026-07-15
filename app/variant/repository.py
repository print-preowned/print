from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business_book.orm import BusinessBookOrm
from app.variant.orm import VariantOrm
from app.variant.schemas import ResolvedConfigRead, VariantCreate, VariantUpdate
from app.variant_config.repository import VariantConfigRepository
from app.variant_option.orm import ProductOptionValueOrm
from app.variant_type.orm import ProductOptionOrm


def effective_price(price: Decimal, discount: Decimal | None) -> float:
    if discount is None:
        return float(price)
    return float(price * (Decimal(1) - discount / Decimal(100)))


class VariantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._config_repo = VariantConfigRepository(session)

    async def create_variant(self, payload: VariantCreate) -> VariantOrm:
        variant = VariantOrm(
            business_book_id=payload.business_book_id,
            description=payload.description,
            stock=payload.stock,
            price=payload.price,
            currency=payload.currency,
            discount=payload.discount,
            sku=payload.sku,
            image=payload.image,
        )
        self._session.add(variant)
        await self._session.flush()
        await self._config_repo.create_variant_product_option_values(
            variant.id, payload.product_option_value_ids
        )
        return variant

    async def update_variant(
        self, variant_id: uuid.UUID, payload: VariantUpdate
    ) -> VariantOrm | None:
        variant = await self.read_variant_by_id(variant_id)
        if variant is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(variant, field, value)
        await self._session.flush()
        return variant

    async def soft_delete_variant(self, variant_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(VariantOrm)
            .where(VariantOrm.id == variant_id, VariantOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(VariantOrm.id)
        )
        if deleted_id is None:
            return False
        await self._config_repo.soft_delete_configs_by_variant_id(variant_id)
        return True

    async def soft_delete_variants_by_business_book(self, business_book_id: uuid.UUID) -> None:
        variant_ids = await self._session.scalars(
            select(VariantOrm.id).where(
                VariantOrm.business_book_id == business_book_id, VariantOrm.deleted_at.is_(None)
            )
        )
        ids = list(variant_ids)
        if not ids:
            return
        await self._session.execute(
            update(VariantOrm)
            .where(VariantOrm.id.in_(ids))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
        )
        await self._config_repo.soft_delete_configs_by_variant_ids(ids)

    async def read_variant_by_id(self, variant_id: uuid.UUID) -> VariantOrm | None:
        return await self._session.scalar(
            select(VariantOrm).where(VariantOrm.id == variant_id, VariantOrm.deleted_at.is_(None))
        )

    async def count_variants(
        self,
        *,
        business_book_id: uuid.UUID | None = None,
        book_id: uuid.UUID | None = None,
        active_catalog_only: bool = False,
    ) -> int:
        statement = (
            select(func.count()).select_from(VariantOrm).where(VariantOrm.deleted_at.is_(None))
        )
        if business_book_id is not None:
            statement = statement.where(VariantOrm.business_book_id == business_book_id)
        if book_id is not None:
            statement = statement.join(
                BusinessBookOrm,
                BusinessBookOrm.id == VariantOrm.business_book_id,
            ).where(
                BusinessBookOrm.book_id == book_id,
                BusinessBookOrm.deleted_at.is_(None),
                BusinessBookOrm.status == "ACTIVE",
            )
        if active_catalog_only:
            statement = statement.where(VariantOrm.status == "ACTIVE", VariantOrm.stock > 0)
        total = await self._session.scalar(statement)
        return int(total or 0)

    async def list_variants(
        self,
        *,
        offset: int,
        limit: int,
        business_book_id: uuid.UUID | None = None,
        book_id: uuid.UUID | None = None,
        active_catalog_only: bool = False,
    ) -> list[VariantOrm]:
        statement: Select[tuple[VariantOrm]] = (
            select(VariantOrm)
            .where(VariantOrm.deleted_at.is_(None))
            .order_by(VariantOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if business_book_id is not None:
            statement = statement.where(VariantOrm.business_book_id == business_book_id)
        if book_id is not None:
            statement = statement.join(
                BusinessBookOrm,
                BusinessBookOrm.id == VariantOrm.business_book_id,
            ).where(
                BusinessBookOrm.book_id == book_id,
                BusinessBookOrm.deleted_at.is_(None),
                BusinessBookOrm.status == "ACTIVE",
            )
        if active_catalog_only:
            statement = statement.where(VariantOrm.status == "ACTIVE", VariantOrm.stock > 0)
        result = await self._session.scalars(statement)
        return list(result)

    async def variant_summary_for_business_books(
        self,
        business_book_ids: list[uuid.UUID],
        *,
        purchasable_only: bool = False,
    ) -> dict[str, dict[str, int | float | None]]:
        if not business_book_ids:
            return {}
        where_clauses = [
            VariantOrm.business_book_id.in_(business_book_ids),
            VariantOrm.deleted_at.is_(None),
        ]
        if purchasable_only:
            where_clauses.extend([VariantOrm.status == "ACTIVE", VariantOrm.stock > 0])
        rows = await self._session.execute(
            select(
                VariantOrm.business_book_id,
                func.count().label("variant_count"),
                func.min(VariantOrm.price).label("min_price"),
                func.sum(VariantOrm.stock).label("total_stock"),
            )
            .where(*where_clauses)
            .group_by(VariantOrm.business_book_id)
        )
        summaries: dict[str, dict[str, int | float | None]] = {}
        for row in rows:
            summaries[str(row.business_book_id)] = {
                "variant_count": int(row.variant_count),
                "min_price": float(row.min_price) if row.min_price is not None else None,
                "total_stock": int(row.total_stock or 0),
            }
        return summaries

    async def read_product_option_values_by_ids(
        self, value_ids: list[uuid.UUID]
    ) -> list[ProductOptionValueOrm]:
        if not value_ids:
            return []
        result = await self._session.scalars(
            select(ProductOptionValueOrm).where(
                ProductOptionValueOrm.id.in_(value_ids), ProductOptionValueOrm.deleted_at.is_(None)
            )
        )
        return list(result)

    async def validate_product_option_values(
        self, value_ids: list[uuid.UUID]
    ) -> list[ProductOptionValueOrm]:
        if not value_ids:
            raise ValueError("At least one variant option is required")
        options = await self.read_product_option_values_by_ids(value_ids)
        if len(options) != len(value_ids):
            raise ValueError("Invalid variant option")
        option_type_ids = [row.product_option_id for row in options]
        if len(option_type_ids) != len(set(option_type_ids)):
            raise ValueError("Only one option per variant type is allowed")
        return options

    async def duplicate_option_set_exists(
        self, business_book_id: uuid.UUID, value_ids: list[uuid.UUID]
    ) -> bool:
        existing_variants = await self._session.scalars(
            select(VariantOrm.id).where(
                VariantOrm.business_book_id == business_book_id, VariantOrm.deleted_at.is_(None)
            )
        )
        variant_ids = list(existing_variants)
        if not variant_ids:
            return False
        config_map = await self.resolve_configs_for_variants(variant_ids)
        target = frozenset((str(value_id) for value_id in value_ids))
        for variant_id in variant_ids:
            existing_values = frozenset(
                (config.variant_option_id for config in config_map.get(variant_id, []))
            )
            if existing_values == target:
                return True
        return False

    async def resolve_configs_for_variants(
        self, variant_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[ResolvedConfigRead]]:
        if not variant_ids:
            return {}
        config_rows = await self._config_repo.read_configs_by_variant_ids(variant_ids)
        if not config_rows:
            return {}
        value_ids = list({row.product_option_value_id for row in config_rows})
        values = await self.read_product_option_values_by_ids(value_ids)
        value_by_id = {row.id: row for row in values}
        type_ids = list({row.product_option_id for row in values})
        types = await self._session.scalars(
            select(ProductOptionOrm).where(
                ProductOptionOrm.id.in_(type_ids), ProductOptionOrm.deleted_at.is_(None)
            )
        )
        type_by_id = {row.id: row for row in types}
        result: dict[uuid.UUID, list[ResolvedConfigRead]] = {}
        for config_row in config_rows:
            value = value_by_id.get(config_row.product_option_value_id)
            if value is None:
                continue
            option_type = type_by_id.get(value.product_option_id)
            if option_type is None:
                continue
            result.setdefault(config_row.variant_id, []).append(
                ResolvedConfigRead(
                    variant_type_id=str(option_type.id),
                    variant_type_name=option_type.name,
                    variant_option_id=str(value.id),
                    variant_option_value=value.value,
                )
            )
        for configs in result.values():
            configs.sort(key=lambda item: item.variant_type_name)
        return result
