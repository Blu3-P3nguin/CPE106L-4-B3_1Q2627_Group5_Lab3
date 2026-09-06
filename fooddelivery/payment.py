"""Developer 4 (part 1): Payment Processing module.

Demonstrates abstraction (ABC) and polymorphism: PaymentProcessor can
drive any PaymentMethod subclass through the same interface.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

from .exceptions import PaymentDeclinedError, RefundError


@dataclass(frozen=True)
class PaymentResult:
    """Outcome of a payment or refund attempt."""

    success: bool
    transaction_id: str
    message: str
    amount: float


class PaymentMethod(ABC):
    """Abstract base class defining the payment gateway interface."""

    def __init__(self) -> None:
        self._processed: Dict[str, float] = {}  # transaction_id -> amount charged

    @abstractmethod
    def process_payment(self, amount: float) -> PaymentResult:
        """Attempt to charge the given amount.

        Must raise PaymentDeclinedError on failure, or return a
        PaymentResult with success=True on success.
        """

    @abstractmethod
    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        """Attempt to refund a previously processed transaction."""

    def _new_transaction_id(self) -> str:
        return f"TXN-{uuid.uuid4().hex[:10]}"

    @property
    def method_name(self) -> str:
        return self.__class__.__name__


class CreditCardPayment(PaymentMethod):
    """Credit card payment gateway (simulated authorization)."""

    def __init__(self, card_number: str, expiry: str, cvv: str) -> None:
        super().__init__()
        digits = card_number.replace(" ", "")
        if len(digits) < 12 or not digits.isdigit():
            raise ValueError("Invalid credit card number.")
        if len(cvv) not in (3, 4) or not cvv.isdigit():
            raise ValueError("Invalid CVV.")
        self._card_last4 = digits[-4:]
        self._expiry = expiry
        self._cvv = cvv

    def process_payment(self, amount: float) -> PaymentResult:
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        # Simulated authorization rule: very large charges get declined.
        if amount > 5000:
            raise PaymentDeclinedError(
                f"Credit card ending in {self._card_last4} declined for "
                f"${amount:.2f} (limit exceeded)."
            )
        txn_id = self._new_transaction_id()
        self._processed[txn_id] = amount
        return PaymentResult(True, txn_id, f"Charged card ending in {self._card_last4}.", amount)

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        charged = self._processed.get(transaction_id)
        if charged is None:
            raise RefundError(f"No such credit card transaction: {transaction_id!r}")
        if amount > charged:
            raise RefundError("Refund amount exceeds original charge.")
        refund_id = self._new_transaction_id()
        return PaymentResult(
            True, refund_id, f"Refunded ${amount:.2f} to card ending in {self._card_last4}.", amount
        )


class DigitalWalletPayment(PaymentMethod):
    """Digital wallet payment gateway (e.g. an app-based balance)."""

    def __init__(self, wallet_id: str, balance: float) -> None:
        super().__init__()
        self._wallet_id = wallet_id
        self._balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    def process_payment(self, amount: float) -> PaymentResult:
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        if amount > self._balance:
            raise PaymentDeclinedError(
                f"Wallet {self._wallet_id} has insufficient balance "
                f"(${self._balance:.2f}) for ${amount:.2f}."
            )
        self._balance -= amount
        txn_id = self._new_transaction_id()
        self._processed[txn_id] = amount
        return PaymentResult(True, txn_id, f"Deducted from wallet {self._wallet_id}.", amount)

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        charged = self._processed.get(transaction_id)
        if charged is None:
            raise RefundError(f"No such wallet transaction: {transaction_id!r}")
        if amount > charged:
            raise RefundError("Refund amount exceeds original charge.")
        self._balance += amount
        refund_id = self._new_transaction_id()
        return PaymentResult(
            True, refund_id, f"Refunded ${amount:.2f} to wallet {self._wallet_id}.", amount
        )


class CashOnDeliveryPayment(PaymentMethod):
    """Cash on delivery: payment is confirmed only when the driver collects it."""

    def process_payment(self, amount: float) -> PaymentResult:
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        txn_id = self._new_transaction_id()
        self._processed[txn_id] = amount
        return PaymentResult(True, txn_id, f"Cash of ${amount:.2f} to be collected on delivery.", amount)

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        charged = self._processed.get(transaction_id)
        if charged is None:
            raise RefundError(f"No such COD transaction: {transaction_id!r}")
        if amount > charged:
            raise RefundError("Refund amount exceeds original charge.")
        refund_id = self._new_transaction_id()
        return PaymentResult(True, refund_id, f"${amount:.2f} marked for cash refund/adjustment.", amount)


class PaymentProcessor:
    """Facade that drives any PaymentMethod polymorphically."""

    def charge(self, method: PaymentMethod, amount: float) -> PaymentResult:
        return method.process_payment(amount)

    def refund(self, method: PaymentMethod, transaction_id: str, amount: float) -> PaymentResult:
        return method.refund(transaction_id, amount)
