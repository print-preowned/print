from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.order_item.model import OrderItemCreateRequest
from app.order.schemas import ORDER_FULFILLMENT_STATUSES

OrderFulfillmentStatus = Literal[
    "PLACED", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"
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
    "ACTIVE": frozenset({"CONFIRMED", "CANCELLED"}),
    "CONFIRMED": frozenset({"SHIPPED", "CANCELLED"}),
    "SHIPPED": frozenset({"DELIVERED"}),
    "DELIVERED": frozenset(),
    "CANCELLED": frozenset(),
}


def assert_valid_order_status_transition(current: str, target: str) -> None:
    if target not in ORDER_FULFILLMENT_STATUSES:
        raise ValueError(f"Invalid order status: {target}")
    allowed = SELLER_ORDER_STATUS_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(f"Cannot transition order from {current} to {target}")
