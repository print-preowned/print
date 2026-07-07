from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.order_item.orm import OrderItemOrm
from app.order_item.schemas import OrderItemCreate, OrderItemUpdate


async def create_order_item(session: AsyncSession, payload: OrderItemCreate) -> OrderItemOrm:
    row = OrderItemOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def update_order_item(
    session: AsyncSession,
    item_id: uuid.UUID,
    payload: OrderItemUpdate,
) -> OrderItemOrm | None:
    row = await read_order_item_by_id(session, item_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_order_item(session: AsyncSession, item_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(OrderItemOrm)
        .where(OrderItemOrm.id == item_id, OrderItemOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(OrderItemOrm.id)
    )
    return deleted_id is not None


async def read_order_item_by_id(session: AsyncSession, item_id: uuid.UUID) -> OrderItemOrm | None:
    return await session.scalar(
        select(OrderItemOrm).where(OrderItemOrm.id == item_id, OrderItemOrm.deleted_at.is_(None))
    )


async def count_order_items(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(OrderItemOrm).where(OrderItemOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_order_items(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[OrderItemOrm]:
    statement: Select[tuple[OrderItemOrm]] = (
        select(OrderItemOrm)
        .where(OrderItemOrm.deleted_at.is_(None))
        .order_by(OrderItemOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)
