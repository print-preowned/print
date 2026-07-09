from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.order.orm import OrderOrm
from app.order.schemas import OrderCreate, OrderUpdate


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_order(self, payload: OrderCreate) -> OrderOrm:
        row = OrderOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_order(self, order_id: uuid.UUID, payload: OrderUpdate) -> OrderOrm | None:
        row = await self.read_order_by_id(order_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def soft_delete_order(self, order_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(OrderOrm)
            .where(OrderOrm.id == order_id, OrderOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(OrderOrm.id)
        )
        return deleted_id is not None

    async def read_order_by_id(self, order_id: uuid.UUID) -> OrderOrm | None:
        return await self._session.scalar(
            select(OrderOrm).where(OrderOrm.id == order_id, OrderOrm.deleted_at.is_(None))
        )

    async def count_orders(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(OrderOrm).where(OrderOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_orders(self, *, offset: int, limit: int) -> list[OrderOrm]:
        statement: Select[tuple[OrderOrm]] = (
            select(OrderOrm)
            .where(OrderOrm.deleted_at.is_(None))
            .order_by(OrderOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
