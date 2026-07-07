from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.variant_config.orm import VariantProductOptionValueOrm
from app.variant_config.schemas import (
    VariantProductOptionValueCreate,
    VariantProductOptionValueUpdate,
)


async def create_variant_product_option_values(
    session: AsyncSession,
    variant_id: uuid.UUID,
    product_option_value_ids: list[uuid.UUID],
) -> list[VariantProductOptionValueOrm]:
    rows: list[VariantProductOptionValueOrm] = []
    for value_id in product_option_value_ids:
        row = VariantProductOptionValueOrm(
            variant_id=variant_id,
            product_option_value_id=value_id,
        )
        session.add(row)
        rows.append(row)
    await session.flush()
    return rows


async def create_variant_product_option_value(
    session: AsyncSession,
    payload: VariantProductOptionValueCreate,
) -> VariantProductOptionValueOrm:
    row = VariantProductOptionValueOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def update_variant_product_option_value(
    session: AsyncSession,
    mapping_id: uuid.UUID,
    payload: VariantProductOptionValueUpdate,
) -> VariantProductOptionValueOrm | None:
    row = await read_variant_product_option_value_by_id(session, mapping_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_variant_product_option_value(
    session: AsyncSession,
    mapping_id: uuid.UUID,
) -> bool:
    deleted_id = await session.scalar(
        update(VariantProductOptionValueOrm)
        .where(
            VariantProductOptionValueOrm.id == mapping_id,
            VariantProductOptionValueOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(VariantProductOptionValueOrm.id)
    )
    return deleted_id is not None


async def soft_delete_configs_by_variant_id(
    session: AsyncSession,
    variant_id: uuid.UUID,
) -> None:
    await session.execute(
        update(VariantProductOptionValueOrm)
        .where(
            VariantProductOptionValueOrm.variant_id == variant_id,
            VariantProductOptionValueOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
    )


async def soft_delete_configs_by_variant_ids(
    session: AsyncSession,
    variant_ids: list[uuid.UUID],
) -> None:
    if not variant_ids:
        return
    await session.execute(
        update(VariantProductOptionValueOrm)
        .where(
            VariantProductOptionValueOrm.variant_id.in_(variant_ids),
            VariantProductOptionValueOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
    )


async def read_variant_product_option_value_by_id(
    session: AsyncSession,
    mapping_id: uuid.UUID,
) -> VariantProductOptionValueOrm | None:
    return await session.scalar(
        select(VariantProductOptionValueOrm).where(
            VariantProductOptionValueOrm.id == mapping_id,
            VariantProductOptionValueOrm.deleted_at.is_(None),
        )
    )


async def read_configs_by_variant_ids(
    session: AsyncSession,
    variant_ids: list[uuid.UUID],
) -> list[VariantProductOptionValueOrm]:
    if not variant_ids:
        return []
    result = await session.scalars(
        select(VariantProductOptionValueOrm).where(
            VariantProductOptionValueOrm.variant_id.in_(variant_ids),
            VariantProductOptionValueOrm.deleted_at.is_(None),
        )
    )
    return list(result)


async def count_variant_product_option_values(session: AsyncSession) -> int:
    from sqlalchemy import func

    total = await session.scalar(
        select(func.count())
        .select_from(VariantProductOptionValueOrm)
        .where(VariantProductOptionValueOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_variant_product_option_values(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[VariantProductOptionValueOrm]:
    from sqlalchemy import Select

    statement: Select[tuple[VariantProductOptionValueOrm]] = (
        select(VariantProductOptionValueOrm)
        .where(VariantProductOptionValueOrm.deleted_at.is_(None))
        .order_by(VariantProductOptionValueOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)
