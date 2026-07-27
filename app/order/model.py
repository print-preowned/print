from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.order_item.model import OrderItemCreateRequest
from app.order.schemas import ORDER_FULFILLMENT_STATUSES

OrderFulfillmentStatus = Literal[
    "PLACED",
    "CONFIRMED",
    "SHIPPED",
    "DELIVERED",
    "READY_FOR_PICKUP",
    "PICKED_UP",
    "CANCELLED",
]


class Order(BaseModel):
    id: str
    user_id: str
    reference: str
    currency: str
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime


class OrderCreateRequest(BaseModel):
    reference: str
    total_amount: float
    fulfillment_type: Literal["DELIVERY", "PICKUP"] = "DELIVERY"
    shipping_address_id: str | None = None
    pickup_location_id: str | None = None
    items: list[OrderItemCreateRequest] = Field(min_length=1)


class OrderUpdateRequest(BaseModel):
    user_id: str | None = None
    reference: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class OrderStatusUpdateRequest(BaseModel):
    status: OrderFulfillmentStatus

    model_config = ConfigDict(extra="forbid")


SELLER_ORDER_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "PLACED": frozenset({"CONFIRMED", "CANCELLED"}),
    "CONFIRMED": frozenset({"SHIPPED", "READY_FOR_PICKUP", "CANCELLED"}),
    "SHIPPED": frozenset({"DELIVERED"}),
    "DELIVERED": frozenset(),
    "READY_FOR_PICKUP": frozenset({"PICKED_UP"}),
    "PICKED_UP": frozenset(),
    "CANCELLED": frozenset(),
}

DELIVERY_FULFILLMENT_STATUSES = frozenset({"SHIPPED", "DELIVERED"})
PICKUP_FULFILLMENT_STATUSES = frozenset({"READY_FOR_PICKUP", "PICKED_UP"})


CUSTOMER_CANCELLABLE_ORDER_STATUSES = frozenset({"PLACED", "CONFIRMED"})


def assert_valid_order_status_transition(
    current: str,
    target: str,
    *,
    fulfillment_type: str = "DELIVERY",
) -> None:
    if target not in ORDER_FULFILLMENT_STATUSES:
        raise ValueError(f"Invalid order status: {target}")
    normalized_fulfillment = fulfillment_type.strip().upper()
    if target in DELIVERY_FULFILLMENT_STATUSES and normalized_fulfillment != "DELIVERY":
        raise ValueError(f"Cannot transition order from {current} to {target}")
    if target in PICKUP_FULFILLMENT_STATUSES and normalized_fulfillment != "PICKUP":
        raise ValueError(f"Cannot transition order from {current} to {target}")
    allowed = SELLER_ORDER_STATUS_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition order from {current} to {target}")


def assert_customer_can_cancel_order(current: str) -> None:
    normalized = current.strip().upper()
    if normalized == "CANCELLED":
        raise ValueError("Order is already cancelled")
    if normalized not in CUSTOMER_CANCELLABLE_ORDER_STATUSES:
        raise ValueError("Order cannot be cancelled after it has shipped")
