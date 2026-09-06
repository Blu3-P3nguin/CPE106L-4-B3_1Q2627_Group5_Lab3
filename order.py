"""Developer 3 (part 1): Order Processing module.

Handles item selection, subtotal/tax/fee calculation, and the order
lifecycle state machine. Delivery tracking lives in delivery.py.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .customer import Address, Customer
from .exceptions import EmptyOrderError, ItemNotFoundError, OrderStateError
from .menu import MenuItem


class OrderStatus(Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    PREPARING = "PREPARING"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# Allowed forward transitions for the order state machine.
_ALLOWED_TRANSITIONS: Dict[OrderStatus, List[OrderStatus]] = {
    OrderStatus.CREATED: [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED],
    OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


@dataclass(frozen=True)
class OrderItem:
    """A line item within an order; the unit price is snapshotted at add-time
    so later menu price changes never retroactively alter existing orders."""

    menu_item: MenuItem
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)


class Order:
    """Represents a customer's food order and its lifecycle state."""

    TAX_RATE = 0.08
    BASE_DELIVERY_FEE = 3.99

    def __init__(self, customer: Customer, delivery_address: Address) -> None:
        self._order_id: str = str(uuid.uuid4())[:8]
        self._customer: Customer = customer
        self._delivery_address: Address = delivery_address
        self._items: List[OrderItem] = []
        self._status: OrderStatus = OrderStatus.CREATED
        self._created_at: datetime = datetime.now()
        self._status_history: List[Tuple[OrderStatus, datetime]] = [
            (self._status, self._created_at)
        ]

    # ---- properties -------------------------------------------------------
    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def delivery_address(self) -> Address:
        return self._delivery_address

    @property
    def items(self) -> List[OrderItem]:
        return list(self._items)

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def status_history(self) -> List[Tuple[OrderStatus, datetime]]:
        return list(self._status_history)

    # ---- item management ---------------------------------------------------
    def add_item(self, menu_item: MenuItem, quantity: int) -> None:
        """Add an item to the order, reserving stock immediately."""
        if self._status != OrderStatus.CREATED:
            raise OrderStateError("Cannot modify items once an order is no longer CREATED.")
        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        if not menu_item.available:
            raise ItemNotFoundError(f"{menu_item.name!r} is currently unavailable.")
        menu_item.reduce_stock(quantity)  # raises OutOfStockError if insufficient
        self._items.append(OrderItem(menu_item, quantity, menu_item.price))

    def remove_item(self, index: int) -> None:
        """Remove a line item from the order by index, restocking it."""
        if self._status != OrderStatus.CREATED:
            raise OrderStateError("Cannot modify items once an order is no longer CREATED.")
        if not 0 <= index < len(self._items):
            raise ItemNotFoundError(f"No item at position {index} in this order.")
        removed = self._items.pop(index)
        removed.menu_item.restock(removed.quantity)

    # ---- calculations -------------------------------------------------------
    def calculate_subtotal(self) -> float:
        return round(sum(item.subtotal for item in self._items), 2)

    def calculate_tax(self) -> float:
        return round(self.calculate_subtotal() * self.TAX_RATE, 2)

    def calculate_delivery_fee(self) -> float:
        return self.BASE_DELIVERY_FEE if self._items else 0.0

    def calculate_total(self) -> float:
        return round(
            self.calculate_subtotal() + self.calculate_tax() + self.calculate_delivery_fee(), 2
        )

    # ---- state machine -------------------------------------------------------
    def _transition(self, new_status: OrderStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS[self._status]
        if new_status not in allowed:
            raise OrderStateError(
                f"Cannot transition order {self._order_id} from "
                f"{self._status.value} to {new_status.value}."
            )
        self._status = new_status
        self._status_history.append((new_status, datetime.now()))

    def mark_paid(self) -> None:
        if not self._items:
            raise EmptyOrderError("Cannot pay for an order with no items.")
        self._transition(OrderStatus.PAID)

    def start_preparing(self) -> None:
        self._transition(OrderStatus.PREPARING)

    def dispatch_for_delivery(self) -> None:
        self._transition(OrderStatus.OUT_FOR_DELIVERY)

    def mark_delivered(self) -> None:
        self._transition(OrderStatus.DELIVERED)

    def cancel(self) -> None:
        """Cancel the order and restock any reserved items."""
        self._transition(OrderStatus.CANCELLED)
        for item in self._items:
            item.menu_item.restock(item.quantity)

    def __repr__(self) -> str:
        return f"Order({self._order_id}, status={self._status.value}, total=${self.calculate_total():.2f})"


class OrderManager:
    """Tracks all orders created in the system."""

    def __init__(self) -> None:
        self._orders: Dict[str, Order] = {}

    def create_order(self, customer: Customer, delivery_address: Optional[Address] = None) -> Order:
        address = delivery_address or customer.get_default_address()
        order = Order(customer, address)
        self._orders[order.order_id] = order
        return order

    def get_order(self, order_id: str) -> Order:
        try:
            return self._orders[order_id]
        except KeyError as exc:
            raise ItemNotFoundError(f"No order with id {order_id!r}") from exc

    def list_orders_by_customer(self, customer_id: str) -> List[Order]:
        return [o for o in self._orders.values() if o.customer.customer_id == customer_id]
