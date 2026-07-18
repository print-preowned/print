from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.orm import BusinessOrm
from app.book.orm import BookOrm
from app.business_book.orm import BusinessBookOrm
from app.order.orm import OrderOrm
from app.order.schemas import OrderCreate, OrderUpdate
from app.order_item.orm import OrderItemOrm
from app.variant.orm import VariantOrm


class CustomerOrderItemRow:
    __slots__ = ("item", "book_title", "book_id", "image", "business_name")

    def __init__(
        self,
        item: OrderItemOrm,
        *,
        book_title: str,
        book_id: uuid.UUID,
        image: str | None,
        business_name: str,
    ) -> None:
        self.item = item
        self.book_title = book_title
        self.book_id = book_id
        self.image = image
        self.business_name = business_name


class BusinessOrderItemRow:
    __slots__ = ("item", "book_title")

    def __init__(self, item: OrderItemOrm, book_title: str) -> None:
        self.item = item
        self.book_title = book_title


class OrderItemPreviewRow:
    __slots__ = ("order_id", "item_id", "book_title", "image", "quantity")

    def __init__(
        self,
        *,
        order_id: uuid.UUID,
        item_id: uuid.UUID,
        book_title: str,
        image: str | None,
        quantity: int,
    ) -> None:
        self.order_id = order_id
        self.item_id = item_id
        self.book_title = book_title
        self.image = image
        self.quantity = quantity


class BusinessOrderTotals(TypedDict):
    item_count: int
    total_amount: Decimal


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

    def _orders_for_user_filter(
        self, user_id: uuid.UUID, *, search: str | None = None
    ) -> Select[tuple[OrderOrm]]:
        statement: Select[tuple[OrderOrm]] = select(OrderOrm).where(
            OrderOrm.deleted_at.is_(None),
            OrderOrm.user_id == user_id,
        )
        if search:
            statement = statement.where(OrderOrm.reference.ilike(f"%{search}%"))
        return statement

    async def count_orders_for_user(
        self, user_id: uuid.UUID, *, search: str | None = None
    ) -> int:
        statement = select(func.count()).select_from(OrderOrm).where(
            OrderOrm.deleted_at.is_(None),
            OrderOrm.user_id == user_id,
        )
        if search:
            statement = statement.where(OrderOrm.reference.ilike(f"%{search}%"))
        total = await self._session.scalar(statement)
        return int(total or 0)

    async def list_orders_for_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
    ) -> list[OrderOrm]:
        statement = (
            self._orders_for_user_filter(user_id, search=search)
            .order_by(OrderOrm.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result)

    async def item_counts_for_orders(
        self, order_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        if not order_ids:
            return {}
        statement = (
            select(OrderItemOrm.order_id, func.count(OrderItemOrm.id))
            .where(
                OrderItemOrm.order_id.in_(order_ids),
                OrderItemOrm.deleted_at.is_(None),
            )
            .group_by(OrderItemOrm.order_id)
        )
        rows = await self._session.execute(statement)
        return {order_id: int(item_count or 0) for order_id, item_count in rows}

    async def preview_items_for_orders(
        self, order_ids: list[uuid.UUID], *, limit_per_order: int = 4
    ) -> dict[uuid.UUID, list[OrderItemPreviewRow]]:
        if not order_ids:
            return {}
        statement = (
            select(
                OrderItemOrm.order_id,
                OrderItemOrm.id,
                OrderItemOrm.quantity,
                BookOrm.title,
                VariantOrm.image,
                BusinessBookOrm.image,
                BookOrm.image,
            )
            .join(VariantOrm, VariantOrm.id == OrderItemOrm.variant_id)
            .join(BusinessBookOrm, BusinessBookOrm.id == VariantOrm.business_book_id)
            .join(BookOrm, BookOrm.id == BusinessBookOrm.book_id)
            .where(
                OrderItemOrm.order_id.in_(order_ids),
                OrderItemOrm.deleted_at.is_(None),
            )
            .order_by(OrderItemOrm.order_id, OrderItemOrm.created_at.asc())
        )
        rows = await self._session.execute(statement)
        previews: dict[uuid.UUID, list[OrderItemPreviewRow]] = {}
        for (
            order_id,
            item_id,
            quantity,
            book_title,
            variant_image,
            listing_image,
            book_image,
        ) in rows:
            bucket = previews.setdefault(order_id, [])
            if len(bucket) >= limit_per_order:
                continue
            bucket.append(
                OrderItemPreviewRow(
                    order_id=order_id,
                    item_id=item_id,
                    book_title=book_title,
                    image=variant_image or listing_image or book_image,
                    quantity=int(quantity),
                )
            )
        return previews

    async def list_customer_order_items(
        self, order_id: uuid.UUID
    ) -> list[CustomerOrderItemRow]:
        statement = (
            select(
                OrderItemOrm,
                BookOrm.title,
                BookOrm.id,
                BusinessOrm.name,
                VariantOrm.image,
                BusinessBookOrm.image,
                BookOrm.image,
            )
            .join(VariantOrm, VariantOrm.id == OrderItemOrm.variant_id)
            .join(BusinessBookOrm, BusinessBookOrm.id == VariantOrm.business_book_id)
            .join(BookOrm, BookOrm.id == BusinessBookOrm.book_id)
            .join(BusinessOrm, BusinessOrm.id == BusinessBookOrm.business_id)
            .where(
                OrderItemOrm.order_id == order_id,
                OrderItemOrm.deleted_at.is_(None),
            )
            .order_by(OrderItemOrm.created_at.asc())
        )
        rows = await self._session.execute(statement)
        return [
            CustomerOrderItemRow(
                item=item,
                book_title=book_title,
                book_id=book_id,
                image=variant_image or listing_image or book_image,
                business_name=business_name,
            )
            for item, book_title, book_id, business_name, variant_image, listing_image, book_image in rows
        ]

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
                "total_amount": Decimal(str(line_total or 0)).quantize(
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
