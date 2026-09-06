"""
Handles customer registration
profile updates
Multiple delivery addresses
Demonstrates encapsulation via private attributes exposed through validated properties
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

from .exceptions import CustomerNotFoundError, InvalidAddressError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ZIP_RE = re.compile(r"^[A-Za-z0-9\- ]{3,12}$")

@dataclass
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    label: str = "Home"

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Raise InvalidAddressError if any required field is missing"""
        missing = [
            field_name
            for field_name, value in (
                ("street", self.street),
                ("city", self.city),
                ("state", self.state),
                ("zip_code", self.zip_code),
            )
            if not value or not str(value).strip()
        ]
        if missing:
            raise InvalidAddressError(
                f"Address is missing required field(s): {', '.join(missing)}"
            )
        if not _ZIP_RE.match(self.zip_code):
            raise InvalidAddressError(f"Invalid zip/postal code: {self.zip_code!r}")

    def __str__(self) -> str:
        return f"{self.label}: {self.street}, {self.city}, {self.state} {self.zip_code}"


class Customer:
    """Represents a registered customer with encapsulated profile data."""

    def __init__(self, name: str, email: str, phone: str) -> None:
        self._customer_id: str = str(uuid.uuid4())[:8]
        self._name: str = self._validate_name(name)
        self._email: str = self._validate_email(email)
        self._phone: str = self._validate_phone(phone)
        self._addresses: List[Address] = []
        self._default_address_index: Optional[int] = None

    """Properties Encapsulation"""
    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = self._validate_name(value)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        self._email = self._validate_email(value)

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        self._phone = self._validate_phone(value)

    @property
    def addresses(self) -> List[Address]:
        """Return a defensive copy of the address list"""
        return list(self._addresses)

    """Validation Helpers"""
    @staticmethod
    def _validate_name(name: str) -> str:
        if not name or not name.strip():
            raise ValueError("Name cannot be empty.")
        return name.strip()

    @staticmethod
    def _validate_email(email: str) -> str:
        if not _EMAIL_RE.match(email or ""):
            raise ValueError(f"Invalid email address: {email!r}")
        return email

    @staticmethod
    def _validate_phone(phone: str) -> str:
        if not phone or not phone.strip():
            raise ValueError("Phone number cannot be empty.")
        return phone.strip()

    """Address Management"""
    def add_address(self, address: Address, make_default: bool = False) -> None:
        address.validate()
        self._addresses.append(address)
        if make_default or self._default_address_index is None:
            self._default_address_index = len(self._addresses) - 1

    def remove_address(self, index: int) -> None:
        if not 0 <= index < len(self._addresses):
            raise InvalidAddressError(f"No address at index {index}.")
        del self._addresses[index]
        if not self._addresses:
            self._default_address_index = None
        elif self._default_address_index is not None and self._default_address_index >= len(self._addresses):
            self._default_address_index = 0

    def set_default_address(self, index: int) -> None:
        if not 0 <= index < len(self._addresses):
            raise InvalidAddressError(f"No address at index {index}.")
        self._default_address_index = index

    def get_default_address(self) -> Address:
        if self._default_address_index is None:
            raise InvalidAddressError("Customer has no delivery addresses on file.")
        return self._addresses[self._default_address_index]

    def update_contact_info(self, name: Optional[str] = None, email: Optional[str] = None,
                             phone: Optional[str] = None) -> None:
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone

    def __repr__(self) -> str:
        return f"Customer({self._customer_id}, {self._name!r}, {self._email!r})"


class CustomerManager:
    def __init__(self) -> None:
        self._customers: Dict[str, Customer] = {}

    def register_customer(self, name: str, email: str, phone: str) -> Customer:
        customer = Customer(name, email, phone)
        self._customers[customer.customer_id] = customer
        return customer

    def get_customer(self, customer_id: str) -> Customer:
        try:
            return self._customers[customer_id]
        except KeyError as exc:
            raise CustomerNotFoundError(f"No customer with id {customer_id!r}") from exc

    def update_customer(self, customer_id: str, **fields) -> Customer:
        customer = self.get_customer(customer_id)
        customer.update_contact_info(**fields)
        return customer

    def list_customers(self) -> List[Customer]:
        return list(self._customers.values())