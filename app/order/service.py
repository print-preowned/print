from __future__ import annotations

import math
import uuid
from decimal import Decimal

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.repository import BusinessRepository
from app.business_address.repository import BusinessAddressRepository
from app.business_book.repository import BusinessBookRepository
from app.order.model import (
    OrderCreateRequest,
    OrderStatusUpdateRequest,
    OrderUpdateRequest,
    assert_customer_can_cancel_order,
    assert_valid_order_status_transition,
)
from app.order_item.model import OrderItemCreateRequest
from app.order.repository import OrderRepository
from app.order.schemas import (
    DEFAULT_ORDER_CURRENCY,
    BusinessOrderDetailRead,
    BusinessOrderItemRead,
    CustomerOrderItemRead,
    OrderCreate,
    OrderDetailRead,
    OrderFulfillmentAddressRead,
    OrderRead,
    OrderSummaryItemPreview,
    OrderSummaryRead,
    OrderUpdate,
)
from app.user_address.repository import UserAddressRepository
from app.utility.address import (
    fulfillment_snapshot_from_business_address,
    fulfillment_snapshot_from_user_address,
)
from app.order_item.repository import OrderItemRepository
from app.order_item.schemas import OrderItemRead
from app.order_item.service import build_order_item_create
from app.utility.model import BaseResponse, PaginatedResponse, Pagination, ParamRequest
from app.utility.service_deps import readable_service, writable_service
from app.variant.repository import VariantRepository, effective_price_decimal


def _parse_id(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid identifier") from exc


def _fulfillment_address_from_row(row) -> OrderFulfillmentAddressRead | None:
    if row.fulfillment_type is None or row.line1 is None:
        return None
    return OrderFulfillmentAddressRead(
        fulfillment_type=row.fulfillment_type,
        recipient_name=row.recipient_name or "",
        address_label=row.address_label,
        phone_number=row.phone_number,
        line1=row.line1,
        line2=row.line2,
        city=row.city or "",
        state=row.state or "",
        postal_code=row.postal_code,
        country_code=row.country_code or "NG",
    )


def _to_read(row) -> OrderRead:
    return OrderRead(
        id=row.id,
        user_id=row.user_id,
        reference=row.reference,
        currency=row.currency,
        total_amount=row.total_amount,
        status=row.status,
        business_id=row.business_id,
        business_name=row.business_name,
        fulfillment_address=_fulfillment_address_from_row(row),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_create(
    payload: OrderCreateRequest,
    user_id: str,
    *,
    total_amount: Decimal,
    business_id: uuid.UUID,
    business_name: str,
    fulfillment_fields: dict[str, str | None],
) -> OrderCreate:
    return OrderCreate(
        user_id=_parse_id(user_id),
        reference=payload.reference,
        currency=DEFAULT_ORDER_CURRENCY,
        total_amount=total_amount,
        business_id=business_id,
        business_name=business_name,
        **fulfillment_fields,  # type: ignore[arg-type]
    )


def _to_item_read(row) -> OrderItemRead:
    return OrderItemRead.model_validate(row)


def _to_detail_read(row, items: list[CustomerOrderItemRead]) -> OrderDetailRead:
    return OrderDetailRead(**_to_read(row).model_dump(), items=items)


def _to_customer_item_read(item_row) -> CustomerOrderItemRead:
    return CustomerOrderItemRead(
        **OrderItemRead.model_validate(item_row.item).model_dump(),
        book_title=item_row.book_title,
        book_id=item_row.book_id,
        image=item_row.image,
        business_name=item_row.business_name,
        author_names=item_row.author_names,
    )


def _to_business_item_read(item_row) -> BusinessOrderItemRead:
    return BusinessOrderItemRead(
        **OrderItemRead.model_validate(item_row.item).model_dump(),
        book_title=item_row.book_title,
        image=item_row.image,
        author_names=item_row.author_names,
    )


def _to_summary_read(
    row,
    *,
    total_amount: Decimal,
    item_count: int,
    preview_items: list[OrderSummaryItemPreview] | None = None,
) -> OrderSummaryRead:
    return OrderSummaryRead(
        id=row.id,
        reference=row.reference,
        currency=row.currency,
        status=row.status,
        total_amount=total_amount,
        item_count=item_count,
        preview_items=preview_items or [],
        business_id=row.business_id,
        business_name=row.business_name,
        fulfillment_address=_fulfillment_address_from_row(row),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OrderRepository(session)
        self._item_repo = OrderItemRepository(session)
        self._variant_repo = VariantRepository(session)
        self._business_book_repo = BusinessBookRepository(session)
        self._business_repo = BusinessRepository(session)
        self._user_address_repo = UserAddressRepository(session)
        self._business_address_repo = BusinessAddressRepository(session)

    async def _read_customer_items(self, order_id: uuid.UUID) -> list[CustomerOrderItemRead]:
        rows = await self._repo.list_customer_order_items(order_id)
        return [_to_customer_item_read(row) for row in rows]

    async def _read_items(self, order_id: uuid.UUID) -> list[OrderItemRead]:
        rows = await self._item_repo.list_order_items_by_order_id(order_id)
        return [_to_item_read(row) for row in rows]

    async def _get_owned_order(self, order_id: uuid.UUID, user_id: str):
        row = await self._repo.read_order_by_id(order_id)
        if row is None or str(row.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Order not found")
        return row

    async def _resolve_order_lines(
        self, items: list[OrderItemCreateRequest]
    ) -> tuple[list[OrderItemCreateRequest], Decimal, uuid.UUID]:
        if not items:
            raise HTTPException(status_code=422, detail="Order must include at least one item")

        quantities: dict[uuid.UUID, int] = {}
        for line in items:
            if line.quantity <= 0:
                raise HTTPException(status_code=422, detail="Item quantity must be positive")
            variant_id = _parse_id(line.variant_id)
            quantities[variant_id] = quantities.get(variant_id, 0) + line.quantity

        resolved: list[OrderItemCreateRequest] = []
        total = Decimal("0")
        business_id: uuid.UUID | None = None

        for variant_id, quantity in quantities.items():
            variant = await self._variant_repo.read_variant_by_id(variant_id)
            if variant is None or variant.status != "ACTIVE":
                raise HTTPException(status_code=422, detail="An item is no longer available")

            listing = await self._business_book_repo.read_business_book_by_id(
                variant.business_book_id
            )
            if listing is None or listing.status != "ACTIVE":
                raise HTTPException(status_code=422, detail="An item is no longer available")

            if business_id is None:
                business_id = listing.business_id
            elif listing.business_id != business_id:
                raise HTTPException(
                    status_code=422,
                    detail="All items must be from the same seller",
                )

            if variant.currency != DEFAULT_ORDER_CURRENCY:
                raise HTTPException(status_code=422, detail="An item has mismatching currency")

            if variant.stock < quantity:
                raise HTTPException(status_code=422, detail="Insufficient stock for an item")

            unit_price = effective_price_decimal(variant.price, variant.discount)
            discount_applied = (
                float(variant.discount)
                if variant.discount is not None
                else None
            )
            resolved.append(
                OrderItemCreateRequest(
                    variant_id=str(variant_id),
                    quantity=quantity,
                    unit_price=float(unit_price),
                    discount_applied=discount_applied,
                )
            )
            total += unit_price * quantity

        assert business_id is not None
        return resolved, total.quantize(Decimal("0.01")), business_id

    async def _create_items(self, order_id: uuid.UUID, lines: list[OrderItemCreateRequest]) -> list:
        item_rows = []
        for line in lines:
            deducted = await self._variant_repo.deduct_stock(
                _parse_id(line.variant_id), line.quantity
            )
            if not deducted:
                raise HTTPException(status_code=422, detail="Insufficient stock for an item")

            item_rows.append(
                await self._item_repo.create_order_item(
                    build_order_item_create(
                        order_id, line, DEFAULT_ORDER_CURRENCY
                    )
                )
            )
        return item_rows

    async def _restore_stock_for_order(self, order_id: uuid.UUID) -> None:
        rows = await self._item_repo.list_order_items_by_order_id(order_id)
        for item in rows:
            await self._variant_repo.restore_stock(item.variant_id, item.quantity)

    async def _cancel_order(self, order_id: uuid.UUID) -> None:
        await self._restore_stock_for_order(order_id)
        updated = await self._repo.update_order(order_id, OrderUpdate(status="CANCELLED"))
        if updated is None:
            raise HTTPException(status_code=404, detail="Order not found")

    async def create(
        self, order: OrderCreateRequest, user_id: str
    ) -> BaseResponse[OrderDetailRead]:
        resolved_lines, total_amount, business_id = await self._resolve_order_lines(order.items)
        client_total = Decimal(str(order.total_amount)).quantize(Decimal("0.01"))
        if client_total != total_amount:
            raise HTTPException(
                status_code=422,
                detail="Cart is out of date. Refresh your cart and try again.",
            )

        business = await self._business_repo.read_by_id(business_id)
        if business is None:
            raise HTTPException(status_code=422, detail="An item is no longer available")

        parsed_user_id = _parse_id(user_id)
        if order.fulfillment_type == "DELIVERY":
            if not order.shipping_address_id:
                raise HTTPException(status_code=422, detail="Delivery address is required")
            address_id = _parse_id(order.shipping_address_id)
            address = await self._user_address_repo.read_by_id(address_id, parsed_user_id)
            if address is None:
                raise HTTPException(status_code=422, detail="Delivery address not found")
            fulfillment_fields = fulfillment_snapshot_from_user_address(address)
        elif order.fulfillment_type == "PICKUP":
            if not order.pickup_location_id:
                raise HTTPException(status_code=422, detail="Pickup location is required")
            location_id = _parse_id(order.pickup_location_id)
            location = await self._business_address_repo.read_by_id(location_id, business_id)
            if location is None or not location.pickup_enabled:
                raise HTTPException(status_code=422, detail="Pickup location not found")
            sole_pickup = await self._business_address_repo.read_pickup_location_by_business(
                business_id
            )
            if sole_pickup is None or sole_pickup.id != location_id:
                raise HTTPException(status_code=422, detail="Pickup location not found")
            fulfillment_fields = fulfillment_snapshot_from_business_address(location)
        else:
            raise HTTPException(status_code=422, detail="Unsupported fulfillment type")
        create_payload = _to_create(
            order,
            user_id,
            total_amount=total_amount,
            business_id=business_id,
            business_name=business.name,
            fulfillment_fields=fulfillment_fields,
        )
        row = await self._repo.create_order(create_payload)
        await self._create_items(row.id, resolved_lines)
        items = await self._read_customer_items(row.id)
        return BaseResponse[OrderDetailRead](
            status_code=201,
            message="Successful",
            data=_to_detail_read(row, items),
        )

    async def update(self, id: str, order: OrderUpdateRequest) -> Response:
        parsed_id = _parse_id(id)
        update_data = order.model_dump(exclude_unset=True)
        if "user_id" in update_data and update_data["user_id"] is not None:
            update_data["user_id"] = _parse_id(str(update_data["user_id"]))
        if "total_amount" in update_data and update_data["total_amount"] is not None:
            update_data["total_amount"] = Decimal(str(update_data["total_amount"]))

        updated = await self._repo.update_order(
            parsed_id,
            OrderUpdate.model_validate(update_data),
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return Response(status_code=200)

    async def delete(self, id: str) -> Response:
        parsed_id = _parse_id(id)
        deleted = await self._repo.soft_delete_order(parsed_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Order not found")
        return Response(status_code=204)

    async def read(self, params: ParamRequest) -> PaginatedResponse[OrderRead]:
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size

        total_results = await self._repo.count_orders()
        rows = await self._repo.list_orders(offset=offset, limit=size)
        data = [_to_read(row) for row in rows]

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[OrderRead](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id(self, id: str, user_id: str | None = None) -> BaseResponse[OrderDetailRead]:
        parsed_id = _parse_id(id)
        row = await self._repo.read_order_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Order not found")
        if user_id is not None and str(row.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Order not found")
        items = await self._read_customer_items(parsed_id)
        return BaseResponse[OrderDetailRead](
            status_code=200,
            message="Successful",
            data=_to_detail_read(row, items),
        )

    async def read_for_customer(
        self, user_id: str, params: ParamRequest
    ) -> PaginatedResponse[OrderSummaryRead]:
        parsed_user_id = _parse_id(user_id)
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        search = (params.search or "").strip() or None

        total_results = await self._repo.count_orders_for_user(
            parsed_user_id, search=search
        )
        rows = await self._repo.list_orders_for_user(
            parsed_user_id,
            offset=offset,
            limit=size,
            search=search,
        )
        item_counts = await self._repo.item_counts_for_orders([row.id for row in rows])
        previews = await self._repo.preview_items_for_orders([row.id for row in rows])
        data = [
            _to_summary_read(
                row,
                total_amount=row.total_amount,
                item_count=int(item_counts.get(row.id, 0)),
                preview_items=[
                    OrderSummaryItemPreview(
                        id=preview.item_id,
                        book_title=preview.book_title,
                        image=preview.image,
                        quantity=preview.quantity,
                    )
                    for preview in previews.get(row.id, [])
                ],
            )
            for row in rows
        ]

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[OrderSummaryRead](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_for_business(
        self, business_id: str, params: ParamRequest
    ) -> PaginatedResponse[OrderSummaryRead]:
        parsed_business_id = _parse_id(business_id)
        page = max(1, params.page)
        size = params.size
        offset = (page - 1) * size
        search = (params.search or "").strip() or None

        total_results = await self._repo.count_orders_for_business(
            parsed_business_id, search=search
        )
        rows = await self._repo.list_orders_for_business(
            parsed_business_id,
            offset=offset,
            limit=size,
            search=search,
        )
        totals = await self._repo.business_totals_for_orders(
            parsed_business_id, [row.id for row in rows]
        )
        data: list[OrderSummaryRead] = []
        for row in rows:
            summary = totals.get(row.id, {})
            raw_total = summary["total_amount"] or Decimal("0.00")
            business_total = (
                raw_total
                if isinstance(raw_total, Decimal)
                else Decimal(str(raw_total)).quantize(Decimal("0.01"))
            )
            data.append(
                _to_summary_read(
                    row,
                    total_amount=business_total,
                    item_count=int(summary["item_count"] or 0),
                )
            )

        total_pages = math.ceil(total_results / size) if size else 1
        return PaginatedResponse[OrderSummaryRead](
            status_code=200,
            message="Successful",
            data=data,
            pagination=Pagination(
                page=page,
                size=size,
                total_pages=total_pages,
                total_results=total_results,
            ),
        )

    async def read_by_id_for_business(
        self, id: str, business_id: str
    ) -> BaseResponse[BusinessOrderDetailRead]:
        parsed_id = _parse_id(id)
        parsed_business_id = _parse_id(business_id)
        row = await self._repo.read_order_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Order not found")
        if not await self._repo.order_belongs_to_business(parsed_id, parsed_business_id):
            raise HTTPException(status_code=404, detail="Order not found")

        item_rows = await self._repo.list_business_order_items(
            parsed_id, parsed_business_id
        )
        totals = await self._repo.business_totals_for_orders(
            parsed_business_id, [parsed_id]
        )
        summary = totals.get(parsed_id, {})
        raw_total = summary.get("total_amount", Decimal("0.00"))
        business_total = (
            raw_total
            if isinstance(raw_total, Decimal)
            else Decimal(str(raw_total)).quantize(Decimal("0.01"))
        )
        items = [_to_business_item_read(item_row) for item_row in item_rows]
        detail = BusinessOrderDetailRead(
            **_to_summary_read(
                row,
                total_amount=business_total,
                item_count=int(summary.get("item_count") or 0),
            ).model_dump(),
            items=items,
        )
        return BaseResponse[BusinessOrderDetailRead](
            status_code=200,
            message="Successful",
            data=detail,
        )

    async def update_status_for_business(
        self, id: str, business_id: str, payload: OrderStatusUpdateRequest
    ) -> Response:
        parsed_id = _parse_id(id)
        parsed_business_id = _parse_id(business_id)
        row = await self._repo.read_order_by_id(parsed_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Order not found")
        if not await self._repo.order_belongs_to_business(parsed_id, parsed_business_id):
            raise HTTPException(status_code=404, detail="Order not found")

        try:
            assert_valid_order_status_transition(
                row.status,
                payload.status,
                fulfillment_type=row.fulfillment_type or "DELIVERY",
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        if payload.status == "CANCELLED":
            await self._cancel_order(parsed_id)
        else:
            updated = await self._repo.update_order(
                parsed_id, OrderUpdate(status=payload.status)
            )
            if updated is None:
                raise HTTPException(status_code=404, detail="Order not found")
        return Response(status_code=204)

    async def cancel_by_customer(self, id: str, user_id: str) -> Response:
        parsed_id = _parse_id(id)
        row = await self._get_owned_order(parsed_id, user_id)
        try:
            assert_customer_can_cancel_order(row.status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        await self._cancel_order(parsed_id)
        return Response(status_code=204)


class WritableOrderService(writable_service(OrderService)):
    pass


class ReadableOrderService(readable_service(OrderService)):
    pass
