"""Order fulfillment status rules."""

from __future__ import annotations

import pytest

from app.order.model import assert_valid_order_status_transition


class TestOrderStatusTransitions:
    def test_placed_to_confirmed(self) -> None:
        assert_valid_order_status_transition("PLACED", "CONFIRMED")

    def test_active_legacy_to_confirmed(self) -> None:
        assert_valid_order_status_transition("ACTIVE", "CONFIRMED")

    def test_delivered_is_terminal(self) -> None:
        with pytest.raises(ValueError, match="Cannot transition"):
            assert_valid_order_status_transition("DELIVERED", "SHIPPED")

    def test_invalid_target_status(self) -> None:
        with pytest.raises(ValueError, match="Invalid order status"):
            assert_valid_order_status_transition("PLACED", "ACTIVE")
