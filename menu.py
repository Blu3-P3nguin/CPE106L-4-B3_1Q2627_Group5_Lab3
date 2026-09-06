"""Developer 2: Menu Catalog & Inventory module.

Manages menu items grouped by category, including pricing, availability
toggling, and stock levels.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Dict, List, Optional

from .exceptions import ItemNotFoundError, OutOfStockError


class MenuCategory(str, Enum):
    APPETIZER = "Appetizer"
    MAIN_COURSE = "Main Course"
    DESSERT = "Dessert"
    BEVERAGE = "Beverage"
    SIDE = "Side"


class MenuItem:
    """A single orderable item, with price and stock encapsulated."""

    def __init__(self, name: str, description: str, price: float,
                 category: MenuCategory, stock_quantity: int = 0,
                 available: bool = True) -> None:
        self._item_id: str = str(uuid.uuid4())[:8]
        self._name: str = name
        self._description: str = description
        self._price: float = self._validate_price(price)
        self._category: MenuCategory = category
        self._stock_quantity: int = max(0, stock_quantity)
        self._available: bool = available  # manual on/off switch (86'd item)

    # ---- properties -------------------------------------------------------
    @property
    def item_id(self) -> str:
        return self._item_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Item name cannot be empty.")
        self._name = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        self._price = self._validate_price(value)

    @property
    def category(self) -> MenuCategory:
        return self._category

    @property
    def stock_quantity(self) -> int:
        return self._stock_quantity

    @property
    def available(self) -> bool:
        """True only if manually enabled AND in stock."""
        return self._available and self._stock_quantity > 0

    # ---- validation -------------------------------------------------------
    @staticmethod
    def _validate_price(price: float) -> float:
        if price < 0:
            raise ValueError("Price cannot be negative.")
        return round(float(price), 2)

    # ---- behavior -----------------------------------------------------------
    def toggle_availability(self) -> None:
        """Manually 86 / un-86 an item regardless of stock level."""
        self._available = not self._available

    def update_price(self, new_price: float) -> None:
        self.price = new_price

    def restock(self, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Restock quantity must be non-negative.")
        self._stock_quantity += quantity

    def reduce_stock(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if quantity > self._stock_quantity:
            raise OutOfStockError(
                f"Only {self._stock_quantity} unit(s) of {self._name!r} remain in stock."
            )
        self._stock_quantity -= quantity

    def __repr__(self) -> str:
        status = "available" if self.available else "unavailable"
        return f"MenuItem({self._name!r}, ${self._price:.2f}, {status})"


class MenuCatalog:
    """Manages the collection of menu items, grouped by category."""

    def __init__(self) -> None:
        self._items: Dict[str, MenuItem] = {}

    def add_item(self, name: str, description: str, price: float,
                 category: MenuCategory, stock_quantity: int = 0) -> MenuItem:
        item = MenuItem(name, description, price, category, stock_quantity)
        self._items[item.item_id] = item
        return item

    def get_item(self, item_id: str) -> MenuItem:
        try:
            return self._items[item_id]
        except KeyError as exc:
            raise ItemNotFoundError(f"No menu item with id {item_id!r}") from exc

    def remove_item(self, item_id: str) -> None:
        if item_id not in self._items:
            raise ItemNotFoundError(f"No menu item with id {item_id!r}")
        del self._items[item_id]

    def update_item(self, item_id: str, **fields) -> MenuItem:
        """Update arbitrary fields on an item, e.g. update_item(id, price=9.99)."""
        item = self.get_item(item_id)
        for key, value in fields.items():
            if key == "price":
                item.update_price(value)
            elif hasattr(item, key):
                setattr(item, key, value)
        return item

    def list_items(self, category: Optional[MenuCategory] = None,
                    only_available: bool = False) -> List[MenuItem]:
        items = list(self._items.values())
        if category is not None:
            items = [i for i in items if i.category == category]
        if only_available:
            items = [i for i in items if i.available]
        return items

    def search(self, keyword: str) -> List[MenuItem]:
        keyword = keyword.lower()
        return [
            i for i in self._items.values()
            if keyword in i.name.lower() or keyword in i.description.lower()
        ]

    def print_menu(self) -> None:
        """Pretty-print the full menu grouped by category."""
        by_category: Dict[MenuCategory, List[MenuItem]] = {}
        for item in self._items.values():
            by_category.setdefault(item.category, []).append(item)
        for category, items in by_category.items():
            print(f"\n== {category.value} ==")
            for item in items:
                mark = "available" if item.available else "sold out/unavailable"
                print(f"  [{item.item_id}] {item.name} - ${item.price:.2f} "
                      f"(stock: {item.stock_quantity}, {mark}) - {item.description}")
