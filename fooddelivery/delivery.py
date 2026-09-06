"""Developer 3 (part 2): Delivery Tracking module.

Assigns available drivers to orders, updates live delivery status, and
estimates delivery times.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from .exceptions import DriverAssignmentError, NoDriverAvailableError, OrderStateError
from .order import Order, OrderStatus


class DriverStatus(Enum):
    AVAILABLE = "AVAILABLE"
    ON_DELIVERY = "ON_DELIVERY"
    OFFLINE = "OFFLINE"


class Driver:
    """A delivery driver with encapsulated availability status."""

    def __init__(self, name: str, phone: str, vehicle: str) -> None:
        self._driver_id: str = str(uuid.uuid4())[:8]
        self._name: str = name
        self._phone: str = phone
        self._vehicle: str = vehicle
        self._status: DriverStatus = DriverStatus.AVAILABLE
        self._current_order_id: Optional[str] = None

    @property
    def driver_id(self) -> str:
        return self._driver_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def vehicle(self) -> str:
        return self._vehicle

    @property
    def status(self) -> DriverStatus:
        return self._status

    @property
    def current_order_id(self) -> Optional[str]:
        return self._current_order_id

    def assign(self, order_id: str) -> None:
        if self._status != DriverStatus.AVAILABLE:
            raise DriverAssignmentError(f"Driver {self._name} is not available.")
        self._status = DriverStatus.ON_DELIVERY
        self._current_order_id = order_id

    def free(self) -> None:
        self._status = DriverStatus.AVAILABLE
        self._current_order_id = None

    def go_offline(self) -> None:
        if self._status == DriverStatus.ON_DELIVERY:
            raise DriverAssignmentError(
                f"Driver {self._name} cannot go offline mid-delivery."
            )
        self._status = DriverStatus.OFFLINE

    def __repr__(self) -> str:
        return f"Driver({self._name}, {self._vehicle}, {self._status.value})"


class DeliveryTracker:
    """Assigns drivers to orders and tracks live delivery status/ETA."""

    AVG_PREP_MINUTES = 15
    AVG_TRANSIT_MINUTES = 20

    def __init__(self) -> None:
        self._drivers: Dict[str, Driver] = {}
        self._eta: Dict[str, datetime] = {}  # order_id -> estimated delivery time

    def register_driver(self, name: str, phone: str, vehicle: str) -> Driver:
        driver = Driver(name, phone, vehicle)
        self._drivers[driver.driver_id] = driver
        return driver

    def _find_available_driver(self) -> Driver:
        for driver in self._drivers.values():
            if driver.status == DriverStatus.AVAILABLE:
                return driver
        raise NoDriverAvailableError("No delivery drivers are currently available.")

    def assign_driver(self, order: Order) -> Driver:
        """Assign the next available driver to an order that is PREPARING."""
        if order.status != OrderStatus.PREPARING:
            raise OrderStateError(
                "A driver can only be assigned once an order is PREPARING."
            )
        driver = self._find_available_driver()
        driver.assign(order.order_id)
        eta_minutes = self.AVG_TRANSIT_MINUTES + random.randint(-5, 10)
        self._eta[order.order_id] = datetime.now() + timedelta(minutes=eta_minutes)
        return driver

    def estimate_delivery_time(self, order: Order) -> datetime:
        if order.order_id in self._eta:
            return self._eta[order.order_id]
        return datetime.now() + timedelta(
            minutes=self.AVG_PREP_MINUTES + self.AVG_TRANSIT_MINUTES
        )

    def complete_delivery(self, driver: Driver) -> None:
        """Free up a driver once their delivery is complete."""
        driver.free()

    def list_drivers(self) -> List[Driver]:
        return list(self._drivers.values())
