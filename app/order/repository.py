from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.book.orm import BookOrm
from app.business_book.orm import BusinessBookOrm
from app.order.orm import OrderOrm
from app.order.schemas import OrderCreate, OrderUpdate
from app.order_item.orm import OrderItemOrm
from app.variant.orm import VariantOrm


class BusinessOrderItemRow:
    __slots__ = ("item", "book_title")

    def __init__(self, item: OrderItemOrm, book_title: str) -> None:
        self.item = item
        self.book_title = book_title


class BusinessOrderTotals(TypedDict):
    item_count: int
    business_total_amount: Decimal


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

    # TODO: optimize this query, traversing 2 extra tables for each order
    def _business_orders_filter(
        self, business_id: uuid.UUID, *, search: str | None = None
    ) -> Select[tuple[OrderOrm]]:
        statement: Select[tuple[OrderOrm]] = (
            select(OrderOrm)
            .join(OrderItemOrm, OrderItemOrm.order_id == OrderOrm.id)
            .join(VariantOrm, VariantOrm.id == OrderItemOrm.variant_id)
            .join(BusinessBookOrm, BusinessBookOrm.id == VariantOrm.business_book_id)
            .where(
                OrderOrm.deleted_at.is_(None),
                OrderItemOrm.deleted_at.is_(None),
                BusinessBookOrm.business_id == business_id,
            )
        )
        if search:
            statement = statement.where(OrderOrm.reference.ilike(f"%{search}%"))
        return statement

    async def count_orders_for_business(
        self, business_id: uuid.UUID, *, search: str | None = None
    ) -> int:
        statement = select(func.count(func.distinct(OrderOrm.id))).select_from(OrderOrm)
        statement = statement.join(
            OrderItemOrm, OrderItemOrm.order_id == OrderOrm.id
        ).join(VariantOrm, VariantOrm.id == OrderItemOrm.variant_id).join(
            BusinessBookOrm, BusinessBookOrm.id == VariantOrm.business_book_id
        ).where(
            OrderOrm.deleted_at.is_(None),
            OrderItemOrm.deleted_at.is_(None),
            BusinessBookOrm.business_id == business_id,
        )
        if search:
            statement = statement.where(OrderOrm.reference.ilike(f"%{search}%"))
        total = await self._session.scalar(statement)
        return int(total or 0)

    async def list_orders_for_business(
        self,
        business_id: uuid.UUID,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
    ) -> list[OrderOrm]:
        statement = (
            self._business_orders_filter(business_id, search=search)
            .group_by(OrderOrm.id)
            .order_by(OrderOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def order_belongs_to_business(
        self, order_id: uuid.UUID, business_id: uuid.UUID
    ) -> bool:
        statement = (
            select(OrderOrm.id)
            .join(OrderItemOrm, OrderItemOrm.order_id == OrderOrm.id)
            .join(VariantOrm, VariantOrm.id == OrderItemOrm.variant_id)
            .join(BusinessBookOrm, BusinessBookOrm.id == VariantOrm.business_book_id)
            .where(
                OrderOrm.id == order_id,
                OrderOrm.deleted_at.is_(None),
                OrderItemOrm.deleted_at.is_(None),
                BusinessBookOrm.business_id == business_id,
            )
            .limit(1)
        )
        found = await self._session.scalar(statement)
        return found is not None

    async def business_totals_for_orders(
        self, business_id: uuid.UUID, order_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, BusinessOrderTotals]:
        if not order_ids:
            return {}
        statement = (
            select(
                OrderItemOrm.order_id,
                func.count(OrderItemOrm.id),
                func.coalesce(
                    func.sum(OrderItemOrm.unit_price * OrderItemOrm.quantity),
                    0,
                ),
            )
            .join(VariantOrm, VariantOrm.id == OrderItemOrm.variant_id)
            .join(BusinessBookOrm, BusinessBookOrm.id == VariantOrm.business_book_id)
            .where(
                OrderItemOrm.order_id.in_(order_ids),
                OrderItemOrm.deleted_at.is_(None),
                BusinessBookOrm.business_id == business_id,
            )
            .group_by(OrderItemOrm.order_id)
        )
        rows = await self._session.execute(statement)
        totals: dict[uuid.UUID, BusinessOrderTotals] = {}
        for order_id, item_count, line_total in rows:
            totals[order_id] = {
                "item_count": int(item_count or 0),
                "business_total_amount": Decimal(str(line_total or 0)).quantize(
                    Decimal("0.01")
                ),
            }
        return totals

    async def list_business_order_items(
        self, order_id: uuid.UUID, business_id: uuid.UUID
    ) -> list[BusinessOrderItemRow]:
        statement = (
            select(OrderItemOrm, BookOrm.title)
            .join(VariantOrm, VariantOrm.id == OrderItemOrm.variant_id)
            .join(BusinessBookOrm, BusinessBookOrm.id == VariantOrm.business_book_id)
            .join(BookOrm, BookOrm.id == BusinessBookOrm.book_id)
            .where(
                OrderItemOrm.order_id == order_id,
                OrderItemOrm.deleted_at.is_(None),
                BusinessBookOrm.business_id == business_id,
            )
            .order_by(OrderItemOrm.created_at.asc())
        )
        rows = await self._session.execute(statement)
        return [
            BusinessOrderItemRow(item=item, book_title=book_title)
            for item, book_title in rows
        ]
