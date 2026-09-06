"""EXCEPTION"""

class FoodDeliveryError(Exception):
    """Base exception for all food delivery system errors."""

class InvalidAddressError(FoodDeliveryError):
    """Raised when a delivery address is invalid or incomplete."""

class CustomerNotFoundError(FoodDeliveryError):
    """Raised when a customer cannot be located in the registry."""

class ItemNotFoundError(FoodDeliveryError):
    """Raised when a menu item (or order) cannot be located."""

class OutOfStockError(FoodDeliveryError):
    """Raised when a requested quantity exceeds available stock."""

class OrderStateError(FoodDeliveryError):
    """Raised when an invalid order state transition is attempted."""

class EmptyOrderError(FoodDeliveryError):
    """Raised when an operation requires a non-empty order."""

class PaymentError(FoodDeliveryError):
    """Base class for payment-related errors."""

class PaymentDeclinedError(PaymentError):
    """Raised when a payment attempt is declined."""

class RefundError(PaymentError):
    """Raised when a refund cannot be processed."""

class NoDriverAvailableError(FoodDeliveryError):
    """Raised when no delivery driver is available for assignment."""

class DriverAssignmentError(FoodDeliveryError):
    """Raised for invalid driver assignment/status operations."""
