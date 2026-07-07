from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.order.orm import OrderOrm
from app.order.schemas import OrderCreate, OrderUpdate


async def create_order(session: AsyncSession, payload: OrderCreate) -> OrderOrm:
    row = OrderOrm(**payload.model_dump())
    session.add(row)
    await session.flush()
    return row


async def update_order(
    session: AsyncSession,
    order_id: uuid.UUID,
    payload: OrderUpdate,
) -> OrderOrm | None:
    row = await read_order_by_id(session, order_id)
    if row is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await session.flush()
    return row


async def soft_delete_order(session: AsyncSession, order_id: uuid.UUID) -> bool:
    deleted_id = await session.scalar(
        update(OrderOrm)
        .where(OrderOrm.id == order_id, OrderOrm.deleted_at.is_(None))
        .values(deleted_at=datetime.now(UTC), status="DELETED")
        .returning(OrderOrm.id)
    )
    return deleted_id is not None


async def read_order_by_id(session: AsyncSession, order_id: uuid.UUID) -> OrderOrm | None:
    return await session.scalar(
        select(OrderOrm).where(OrderOrm.id == order_id, OrderOrm.deleted_at.is_(None))
    )


async def count_orders(session: AsyncSession) -> int:
    total = await session.scalar(
        select(func.count()).select_from(OrderOrm).where(OrderOrm.deleted_at.is_(None))
    )
    return int(total or 0)


async def list_orders(
    session: AsyncSession,
    *,
    offset: int,
    limit: int,
) -> list[OrderOrm]:
    statement: Select[tuple[OrderOrm]] = (
        select(OrderOrm)
        .where(OrderOrm.deleted_at.is_(None))
        .order_by(OrderOrm.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.scalars(statement)
    return list(result)
