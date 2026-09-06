"""Developer 4 (part 2): Completed Transaction Reporting module.

Stores immutable audit-log records of successful orders, generates
itemized receipts, and supports querying past transaction history.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Tuple

from .order import Order


@dataclass(frozen=True)
class TransactionLineItem:
    """Immutable snapshot of an ordered item for the receipt."""

    name: str
    quantity: int
    unit_price: float
    subtotal: float


@dataclass(frozen=True)
class TransactionRecord:
    """An immutable audit-log record of a successfully completed order.

    Being a frozen dataclass, once created a record can never be mutated,
    which is what makes it suitable as an audit log entry.
    """

    transaction_id: str
    order_id: str
    customer_id: str
    customer_name: str
    line_items: Tuple[TransactionLineItem, ...]
    subtotal: float
    tax: float
    delivery_fee: float
    total: float
    payment_method: str
    payment_transaction_id: str
    timestamp: datetime

    def to_receipt(self) -> str:
        """Render a human-readable itemized receipt."""
        lines = [
            "=" * 46,
            "          COMPLETED TRANSACTION RECEIPT",
            "=" * 46,
            f"Transaction ID : {self.transaction_id}",
            f"Order ID       : {self.order_id}",
            f"Customer       : {self.customer_name} ({self.customer_id})",
            f"Date           : {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "-" * 46,
        ]
        for item in self.line_items:
            lines.append(
                f"{item.quantity} x {item.name:<20} ${item.unit_price:>6.2f}  = ${item.subtotal:>7.2f}"
            )
        lines += [
            "-" * 46,
            f"{'Subtotal':<32}${self.subtotal:>10.2f}",
            f"{'Tax':<32}${self.tax:>10.2f}",
            f"{'Delivery Fee':<32}${self.delivery_fee:>10.2f}",
            f"{'TOTAL':<32}${self.total:>10.2f}",
            "-" * 46,
            f"Paid via {self.payment_method} (ref: {self.payment_transaction_id})",
            "=" * 46,
        ]
        return "\n".join(lines)


class TransactionLog:
    """Append-only, immutable audit log of completed transactions."""

    def __init__(self) -> None:
        self._records: List[TransactionRecord] = []

    def record_transaction(self, order: Order, payment_method_name: str,
                            payment_transaction_id: str) -> TransactionRecord:
        """Create and store an immutable transaction record from a completed order."""
        line_items = tuple(
            TransactionLineItem(
                name=item.menu_item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in order.items
        )
        record = TransactionRecord(
            transaction_id=f"RCPT-{uuid.uuid4().hex[:10]}",
            order_id=order.order_id,
            customer_id=order.customer.customer_id,
            customer_name=order.customer.name,
            line_items=line_items,
            subtotal=order.calculate_subtotal(),
            tax=order.calculate_tax(),
            delivery_fee=order.calculate_delivery_fee(),
            total=order.calculate_total(),
            payment_method=payment_method_name,
            payment_transaction_id=payment_transaction_id,
            timestamp=datetime.now(),
        )
        self._records.append(record)
        return record

    def get_receipt(self, transaction_id: str) -> Optional[TransactionRecord]:
        for record in self._records:
            if record.transaction_id == transaction_id:
                return record
        return None

    def get_history_by_customer(self, customer_id: str) -> List[TransactionRecord]:
        return [r for r in self._records if r.customer_id == customer_id]

    def get_history_by_date(self, target_date: date) -> List[TransactionRecord]:
        return [r for r in self._records if r.timestamp.date() == target_date]

    def all_records(self) -> List[TransactionRecord]:
        return list(self._records)
