from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.order_item.orm import OrderItemOrm
from app.order_item.schemas import OrderItemCreate, OrderItemUpdate


class OrderItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_order_item(self, payload: OrderItemCreate) -> OrderItemOrm:
        row = OrderItemOrm(**payload.model_dump())
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_order_item(
        self, item_id: uuid.UUID, payload: OrderItemUpdate
    ) -> OrderItemOrm | None:
        row = await self.read_order_item_by_id(item_id)
        if row is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        await self._session.flush()
        return row

    async def delete_order_item(self, item_id: uuid.UUID) -> bool:
        deleted_id = await self._session.scalar(
            update(OrderItemOrm)
            .where(OrderItemOrm.id == item_id, OrderItemOrm.deleted_at.is_(None))
            .values(deleted_at=datetime.now(UTC), status="DELETED")
            .returning(OrderItemOrm.id)
        )
        return deleted_id is not None

    async def read_order_item_by_id(self, item_id: uuid.UUID) -> OrderItemOrm | None:
        return await self._session.scalar(
            select(OrderItemOrm).where(
                OrderItemOrm.id == item_id, OrderItemOrm.deleted_at.is_(None)
            )
        )

    async def list_order_items_by_order_id(self, order_id: uuid.UUID) -> list[OrderItemOrm]:
        statement: Select[tuple[OrderItemOrm]] = (
            select(OrderItemOrm)
            .where(
                OrderItemOrm.order_id == order_id,
                OrderItemOrm.deleted_at.is_(None),
            )
            .order_by(OrderItemOrm.created_at.asc())
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def count_order_items(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(OrderItemOrm).where(OrderItemOrm.deleted_at.is_(None))
        )
        return int(total or 0)

    async def list_order_items(self, *, offset: int, limit: int) -> list[OrderItemOrm]:
        statement: Select[tuple[OrderItemOrm]] = (
            select(OrderItemOrm)
            .where(OrderItemOrm.deleted_at.is_(None))
            .order_by(OrderItemOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)
