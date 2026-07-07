from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.variant.orm import VariantOrm
from app.variant.schemas import ResolvedConfigRead, VariantCreate, VariantUpdate
from app.variant_config.orm import VariantProductOptionValueOrm
from app.variant_config.repository import (
    create_variant_product_option_values,
    read_configs_by_variant_ids,
    soft_delete_configs_by_variant_id,
    soft_delete_configs_by_variant_ids,
)
from app.variant_option.orm import ProductOptionValueOrm
from app.variant_type.orm import ProductOptionOrm


async def create_variant(
    session: AsyncSession,
    payload: VariantCreate,
) -> VariantOrm:
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
    session.add(variant)
    await session.flush()
    await create_variant_product_option_values(
        session,
        variant.id,
        payload.product_option_value_ids,
    )
    return variant


async def update_variant(
    session: AsyncSession,
    variant_id: uuid.UUID,
    payload: VariantUpdate,
) -> VariantOrm | None:
    variant = await read_variant_by_id(session, variant_id)
    if variant is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(variant, field, value)
    await session.flush()
    return variant


async def soft_delete_variant(session: AsyncSession, variant_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(VariantOrm)
        .where(VariantOrm.id == variant_id, VariantOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(VariantOrm.id)
    )
    if deleted_id is None:
        return False
    await soft_delete_configs_by_variant_id(session, variant_id)
    return True


async def soft_delete_variants_by_business_book(
    session: AsyncSession,
    business_book_id: uuid.UUID,
) -> None:
    variant_ids = await session.scalars(
        select(VariantOrm.id).where(
            VariantOrm.business_book_id == business_book_id,
            VariantOrm.deleted_at.is_(None),
        )
    )
    ids = list(variant_ids)
    if not ids:
        return
    await session.execute(
        update(VariantOrm)
        .where(VariantOrm.id.in_(ids))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
    )
    await soft_delete_configs_by_variant_ids(session, ids)


async def read_variant_by_id(session: AsyncSession, variant_id: uuid.UUID) -> VariantOrm | None:
    return await session.scalar(
        select(VariantOrm).where(
            VariantOrm.id == variant_id,
            VariantOrm.deleted_at.is_(None),
        )
    )


async def count_variants(
    session: AsyncSession,
    *,
    business_book_id: uuid.UUID | None = None,
    active_catalog_only: bool = False,
) -> int:
    statement = (
        select(func.count())
        .select_from(VariantOrm)
        .where(VariantOrm.deleted_at.is_(None))
    )
    if business_book_id is not None:
        statement = statement.where(VariantOrm.business_book_id == business_book_id)
    if active_catalog_only:
        statement = statement.where(VariantOrm.status == "ACTIVE", VariantOrm.stock > 0)
    total = await session.scalar(statement)
    return int(total or 0)


async def list_variants(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
    business_book_id: uuid.UUID | None = None,
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
    if active_catalog_only:
        statement = statement.where(VariantOrm.status == "ACTIVE", VariantOrm.stock > 0)
    result = await session.scalars(statement)
    return list(result)


async def variant_summary_for_business_books(
    session: AsyncSession,
    business_book_ids: list[uuid.UUID],
) -> dict[str, dict[str, int | float | None]]:
    if not business_book_ids:
        return {}
    rows = await session.execute(
        select(
            VariantOrm.business_book_id,
            func.count().label("variant_count"),
            func.min(VariantOrm.price).label("min_price"),
            func.sum(VariantOrm.stock).label("total_stock"),
        )
        .where(
            VariantOrm.business_book_id.in_(business_book_ids),
            VariantOrm.deleted_at.is_(None),
        )
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
    session: AsyncSession,
    value_ids: list[uuid.UUID],
) -> list[ProductOptionValueOrm]:
    if not value_ids:
        return []
    result = await session.scalars(
        select(ProductOptionValueOrm).where(
            ProductOptionValueOrm.id.in_(value_ids),
            ProductOptionValueOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def validate_product_option_values(
    session: AsyncSession,
    value_ids: list[uuid.UUID],
) -> list[ProductOptionValueOrm]:
    if not value_ids:
        raise ValueError("At least one variant option is required")
    options = await read_product_option_values_by_ids(session, value_ids)
    if len(options) != len(value_ids):
        raise ValueError("Invalid variant option")
    option_type_ids = [row.product_option_id for row in options]
    if len(option_type_ids) != len(set(option_type_ids)):
        raise ValueError("Only one option per variant type is allowed")
    return options


async def duplicate_option_set_exists(
    session: AsyncSession,
    business_book_id: uuid.UUID,
    value_ids: list[uuid.UUID],
) -> bool:
    existing_variants = await session.scalars(
        select(VariantOrm.id).where(
            VariantOrm.business_book_id == business_book_id,
            VariantOrm.deleted_at.is_(None),
        )
    )
    variant_ids = list(existing_variants)
    if not variant_ids:
        return False
    config_map = await resolve_configs_for_variants(session, variant_ids)
    target = frozenset(str(value_id) for value_id in value_ids)
    for variant_id in variant_ids:
        existing_values = frozenset(
            config.variant_option_id for config in config_map.get(variant_id, [])
        )
        if existing_values == target:
            return True
    return False


async def resolve_configs_for_variants(
    session: AsyncSession,
    variant_ids: list[uuid.UUID],
) -> dict[uuid.UUID, list[ResolvedConfigRead]]:
    if not variant_ids:
        return {}
    config_rows = await read_configs_by_variant_ids(session, variant_ids)
    if not config_rows:
        return {}

    value_ids = list({row.product_option_value_id for row in config_rows})
    values = await read_product_option_values_by_ids(session, value_ids)
    value_by_id = {row.id: row for row in values}

    type_ids = list({row.product_option_id for row in values})
    types = await session.scalars(
        select(ProductOptionOrm).where(
            ProductOptionOrm.id.in_(type_ids),
            ProductOptionOrm.deleted_at.is_(None),
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


def effective_price(price: Decimal, discount: Decimal | None) -> float:
    if discount is None:
        return float(price)
    return float(price * (Decimal(1) - discount / Decimal(100)))
