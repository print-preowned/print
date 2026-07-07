from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.variant_type.orm import ProductOptionOrm
from app.variant_type.schemas import ProductOptionCreate, ProductOptionUpdate


async def create_product_option(
    session: AsyncSession,
    payload: ProductOptionCreate,
) -> ProductOptionOrm:
    row = ProductOptionOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def update_product_option(
    session: AsyncSession,
    product_option_id: uuid.UUID,
    payload: ProductOptionUpdate,
) -> ProductOptionOrm | None:
    row = await read_product_option_by_id(session, product_option_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_product_option(session: AsyncSession, product_option_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(ProductOptionOrm)
        .where(
            ProductOptionOrm.id == product_option_id,
            ProductOptionOrm.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(ProductOptionOrm.id)
    )
    return deleted_id is not None


async def read_product_option_by_id(
    session: AsyncSession,
    product_option_id: uuid.UUID,
) -> ProductOptionOrm | None:
    return await session.scalar(
        select(ProductOptionOrm).where(
            ProductOptionOrm.id == product_option_id,
            ProductOptionOrm.deleted_at.is_(None),
        )
    )


async def read_product_option_by_name(
    session: AsyncSession,
    name: str,
) -> ProductOptionOrm | None:
    return await session.scalar(
        select(ProductOptionOrm).where(
            ProductOptionOrm.name == name,
            ProductOptionOrm.deleted_at.is_(None),
        )
    )


async def count_product_options(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(ProductOptionOrm).where(ProductOptionOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_product_options(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[ProductOptionOrm]:
    statement: Select[tuple[ProductOptionOrm]] = (
        select(ProductOptionOrm)
        .where(ProductOptionOrm.deleted_at.is_(None))
        .order_by(ProductOptionOrm.name)
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)
