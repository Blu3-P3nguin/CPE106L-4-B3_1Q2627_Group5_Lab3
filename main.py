"""
Food Delivery System — Interactive Terminal Application
=========================================================
Run this and YOU are the customer: register, browse the menu, build
an order, pay, track your delivery live, and view your receipt —
all driven by your own input at the terminal.

    python3 main.py
"""
from __future__ import annotations

import sys
from typing import List, Optional, Tuple

from fooddelivery import (
    Address,
    CashOnDeliveryPayment,
    CreditCardPayment,
    Customer,
    CustomerManager,
    DeliveryTracker,
    DigitalWalletPayment,
    Driver,
    MenuCatalog,
    MenuCategory,
    MenuItem,
    Order,
    OrderManager,
    PaymentMethod,
    PaymentProcessor,
    PaymentResult,
    TransactionLog,
)
from fooddelivery.exceptions import FoodDeliveryError

DIVIDER = "-" * 50


# ==========================================================================
# Small input helpers
# ==========================================================================
def ask(prompt: str) -> str:
    """Read a line of input, exiting cleanly on Ctrl-C / Ctrl-D."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nGoodbye!")
        sys.exit(0)


def ask_nonempty(prompt: str) -> str:
    while True:
        value = ask(prompt)
        if value:
            return value
        print("  This field can't be empty. Please try again.")


def ask_choice(prompt: str, choices: List[str]) -> str:
    choice_str = "/".join(choices)
    while True:
        value = ask(f"{prompt} [{choice_str}]: ").lower()
        if value in choices:
            return value
        print(f"  Please enter one of: {choice_str}")


def ask_int(prompt: str, min_value: int = 1, max_value: Optional[int] = None) -> int:
    while True:
        raw = ask(prompt)
        try:
            value = int(raw)
        except ValueError:
            print("  Please enter a whole number.")
            continue
        if value < min_value or (max_value is not None and value > max_value):
            bound = f"{min_value}-{max_value}" if max_value is not None else f">= {min_value}"
            print(f"  Please enter a number in range {bound}.")
            continue
        return value


def ask_float(prompt: str, min_value: float = 0.0) -> float:
    while True:
        raw = ask(prompt)
        try:
            value = float(raw)
        except ValueError:
            print("  Please enter a number.")
            continue
        if value < min_value:
            print(f"  Please enter a value >= {min_value}.")
            continue
        return value


def pause() -> None:
    ask("\n(press Enter to continue) ")


def header(title: str) -> None:
    print(f"\n{DIVIDER}\n{title}\n{DIVIDER}")


# ==========================================================================
# "Restaurant side" seed data — pretend this was already set up by the
# menu/inventory and delivery teams before the app launched.
# ==========================================================================
def seed_menu(catalog: MenuCatalog) -> None:
    catalog.add_item("Margherita Pizza", "Classic tomato & mozzarella",
                      12.99, MenuCategory.MAIN_COURSE, stock_quantity=20)
    catalog.add_item("Pepperoni Pizza", "Loaded with pepperoni",
                      14.49, MenuCategory.MAIN_COURSE, stock_quantity=15)
    catalog.add_item("Caesar Salad", "Romaine, parmesan, croutons",
                      8.50, MenuCategory.APPETIZER, stock_quantity=15)
    catalog.add_item("Mozzarella Sticks", "Crispy, served with marinara",
                      6.99, MenuCategory.APPETIZER, stock_quantity=12)
    catalog.add_item("Garlic Bread", "Toasted with garlic butter",
                      4.25, MenuCategory.SIDE, stock_quantity=25)
    catalog.add_item("French Fries", "Crispy golden fries",
                      3.75, MenuCategory.SIDE, stock_quantity=30)
    catalog.add_item("Tiramisu", "Coffee-soaked ladyfingers",
                      6.75, MenuCategory.DESSERT, stock_quantity=10)
    catalog.add_item("Chocolate Lava Cake", "Warm cake, molten center",
                      7.25, MenuCategory.DESSERT, stock_quantity=8)
    catalog.add_item("Iced Tea", "Freshly brewed, unsweetened",
                      2.50, MenuCategory.BEVERAGE, stock_quantity=30)
    catalog.add_item("Sparkling Water", "Chilled, 500ml",
                      2.00, MenuCategory.BEVERAGE, stock_quantity=40)


def seed_drivers(tracker: DeliveryTracker) -> None:
    tracker.register_driver("Alex Rivera", "555-0100", "Scooter")
    tracker.register_driver("Jamie Chen", "555-0101", "Bicycle")
    tracker.register_driver("Sam Okafor", "555-0102", "Car")


# ==========================================================================
# Onboarding: registration & addresses
# ==========================================================================
def registration_flow(customer_manager: CustomerManager) -> Customer:
    header("LET'S GET YOU SET UP")
    print("Please create your customer profile.")
    while True:
        name = ask_nonempty("\nFull name: ")
        email = ask_nonempty("Email: ")
        phone = ask_nonempty("Phone number: ")
        try:
            customer = customer_manager.register_customer(name, email, phone)
            print(f"\nWelcome, {customer.name}! Your customer ID is {customer.customer_id}.")
            return customer
        except ValueError as exc:
            print(f"  Error: {exc} Please try again.")


def add_address_flow(customer: Customer, required: bool = False) -> None:
    header("ADD A DELIVERY ADDRESS")
    if required:
        print("You'll need at least one delivery address before ordering.")
    while True:
        street = ask_nonempty("\nStreet address: ")
        city = ask_nonempty("City: ")
        state = ask_nonempty("State/Province: ")
        zip_code = ask_nonempty("Zip/Postal code: ")
        label = ask("Label (Home/Work/etc., default 'Home'): ") or "Home"
        try:
            address = Address(street, city, state, zip_code, label)
            make_default = (not customer.addresses) or ask_choice(
                "Set as default address?", ["y", "n"]) == "y"
            customer.add_address(address, make_default=make_default)
            print(f"\nAddress saved: {address}")
            break
        except FoodDeliveryError as exc:
            print(f"  Error: {exc} Please try again.")

    if ask_choice("\nAdd another address?", ["y", "n"]) == "y":
        add_address_flow(customer)


# ==========================================================================
# Account management
# ==========================================================================
def account_menu(customer: Customer) -> None:
    while True:
        header("MY ACCOUNT")
        print(f"Name:  {customer.name}")
        print(f"Email: {customer.email}")
        print(f"Phone: {customer.phone}")
        print("\nAddresses:")
        if not customer.addresses:
            print("  (none on file)")
        else:
            default = customer.get_default_address()
            for i, addr in enumerate(customer.addresses):
                marker = " (default)" if addr is default else ""
                print(f"  {i + 1}. {addr}{marker}")

        print("\n1. Update contact info")
        print("2. Add a new address")
        print("3. Set default address")
        print("4. Back to main menu")
        choice = ask_choice("Choose an option", ["1", "2", "3", "4"])

        if choice == "1":
            name = ask("New name (leave blank to keep current): ")
            email = ask("New email (leave blank to keep current): ")
            phone = ask("New phone (leave blank to keep current): ")
            try:
                customer.update_contact_info(
                    name=name or None, email=email or None, phone=phone or None
                )
                print("Profile updated.")
            except ValueError as exc:
                print(f"  Error: {exc}")
        elif choice == "2":
            add_address_flow(customer)
        elif choice == "3":
            if not customer.addresses:
                print("You have no addresses yet.")
                continue
            idx = ask_int(f"Address number (1-{len(customer.addresses)}): ",
                           1, len(customer.addresses))
            customer.set_default_address(idx - 1)
            print("Default address updated.")
        else:
            return


# ==========================================================================
# Menu browsing
# ==========================================================================
def view_menu(catalog: MenuCatalog) -> None:
    header("MENU")
    for category in MenuCategory:
        items = catalog.list_items(category=category)
        if not items:
            continue
        print(f"\n{category.value}")
        for item in items:
            status = "" if item.available else "  (currently unavailable)"
            print(f"  {item.name:<22} ${item.price:>6.2f}{status}")
            print(f"    {item.description}")


def numbered_available_items(catalog: MenuCatalog) -> List[MenuItem]:
    items = [item for item in catalog.list_items() if item.available]
    print()
    for i, item in enumerate(items):
        print(f"  {i + 1}. {item.name:<22} ${item.price:>6.2f}  ({item.category.value})")
    return items


# ==========================================================================
# Cart / order building
# ==========================================================================
def print_cart(order: Order) -> None:
    print()
    for i, item in enumerate(order.items):
        print(f"  {i + 1}. {item.quantity} x {item.menu_item.name:<20} "
              f"${item.unit_price:>6.2f}  = ${item.subtotal:>7.2f}")
    print(f"\n  Subtotal: ${order.calculate_subtotal():.2f}")
    print(f"  Tax:      ${order.calculate_tax():.2f}")
    print(f"  Delivery: ${order.calculate_delivery_fee():.2f}")
    print(f"  Total:    ${order.calculate_total():.2f}")


def build_order_flow(order_manager: OrderManager, catalog: MenuCatalog,
                      customer: Customer) -> Optional[Order]:
    order = order_manager.create_order(customer)
    print(f"\nStarted a new order for delivery to: {order.delivery_address}")

    while True:
        header("BUILD YOUR ORDER")
        if order.items:
            print_cart(order)
        else:
            print("Your cart is empty.")

        print("\n1. Add item")
        print("2. Remove item")
        print("3. View full menu")
        print("4. Checkout")
        print("5. Cancel this order")
        choice = ask_choice("Choose an option", ["1", "2", "3", "4", "5"])

        if choice == "1":
            items = numbered_available_items(catalog)
            if not items:
                print("Sorry, nothing is available right now.")
                continue
            idx = ask_int(f"Item number (1-{len(items)}): ", 1, len(items))
            qty = ask_int("Quantity: ", 1)
            try:
                order.add_item(items[idx - 1], qty)
                print(f"Added {qty} x {items[idx - 1].name} to your order.")
            except FoodDeliveryError as exc:
                print(f"  Couldn't add item: {exc}")

        elif choice == "2":
            if not order.items:
                print("Your cart is already empty.")
                continue
            print_cart(order)
            idx = ask_int(f"\nItem number to remove (1-{len(order.items)}): ",
                           1, len(order.items))
            try:
                order.remove_item(idx - 1)
                print("Item removed.")
            except FoodDeliveryError as exc:
                print(f"  Couldn't remove item: {exc}")

        elif choice == "3":
            view_menu(catalog)

        elif choice == "4":
            if not order.items:
                print("Add at least one item before checking out.")
                continue
            return order

        else:
            order.cancel()
            print("Order cancelled.")
            return None


# ==========================================================================
# Checkout / payment
# ==========================================================================
def checkout_flow(order: Order,
                   payment_processor: PaymentProcessor
                   ) -> Tuple[Optional[PaymentMethod], Optional[PaymentResult]]:
    header("CHECKOUT")
    print_cart(order)
    total = order.calculate_total()

    while True:
        print("\nPayment method:")
        print("  1. Credit Card")
        print("  2. Digital Wallet")
        print("  3. Cash on Delivery")
        choice = ask_choice("Choose an option", ["1", "2", "3"])

        try:
            if choice == "1":
                number = ask_nonempty("Card number: ")
                expiry = ask_nonempty("Expiry (MM/YY): ")
                cvv = ask_nonempty("CVV: ")
                method: PaymentMethod = CreditCardPayment(number, expiry, cvv)
            elif choice == "2":
                wallet_id = ask_nonempty("Wallet ID: ")
                balance = ask_float("Current wallet balance: $")
                method = DigitalWalletPayment(wallet_id, balance)
            else:
                method = CashOnDeliveryPayment()

            result = payment_processor.charge(method, total)
            order.mark_paid()
            print(f"\n[PAID] {result.message} (ref: {result.transaction_id})")
            return method, result

        except FoodDeliveryError as exc:
            print(f"\n[DECLINED] {exc}")
            if ask_choice("Try a different payment method?", ["y", "n"]) == "n":
                return None, None
        except ValueError as exc:
            print(f"\n  Invalid input: {exc}")


# ==========================================================================
# Live delivery tracking
# ==========================================================================
def fulfillment_flow(order: Order, delivery_tracker: DeliveryTracker) -> Optional[Driver]:
    header("ORDER STATUS")
    print(f"Order {order.order_id} received! Status: {order.status.value}")
    pause()

    order.start_preparing()
    print(f"\nThe kitchen is now preparing your order. Status: {order.status.value}")
    pause()

    try:
        driver = delivery_tracker.assign_driver(order)
    except FoodDeliveryError as exc:
        print(f"\n{exc}")
        print("Your order will be dispatched as soon as a driver is free.")
        return None

    order.dispatch_for_delivery()
    eta = delivery_tracker.estimate_delivery_time(order)
    print(f"\n{driver.name} ({driver.vehicle}) is on the way with your order!")
    print(f"Status: {order.status.value}")
    print(f"Estimated arrival: {eta.strftime('%I:%M %p')}")
    pause()

    order.mark_delivered()
    delivery_tracker.complete_delivery(driver)
    print(f"\nDelivered! Status: {order.status.value}")
    print("Enjoy your meal!")
    return driver


# ==========================================================================
# Receipts & history
# ==========================================================================
def receipt_flow(order: Order, transaction_log: TransactionLog,
                  method: PaymentMethod, result: PaymentResult) -> None:
    header("RECEIPT")
    record = transaction_log.record_transaction(order, method.method_name, result.transaction_id)
    print(record.to_receipt())


def order_history_flow(transaction_log: TransactionLog, customer: Customer) -> None:
    header("MY ORDER HISTORY")
    records = transaction_log.get_history_by_customer(customer.customer_id)
    if not records:
        print("You haven't completed any orders yet.")
        return
    for i, record in enumerate(records):
        print(f"{i + 1}. {record.timestamp.strftime('%Y-%m-%d %H:%M')} - "
              f"Order {record.order_id} - ${record.total:.2f}")
    choice = ask("\nEnter a number to view the full receipt, or press Enter to go back: ")
    if choice.isdigit() and 1 <= int(choice) <= len(records):
        print()
        print(records[int(choice) - 1].to_receipt())


# ==========================================================================
# Main application loop
# ==========================================================================
def main() -> None:
    # System state — set up once as if by the other three dev teams.
    customer_manager = CustomerManager()
    menu_catalog = MenuCatalog()
    order_manager = OrderManager()
    delivery_tracker = DeliveryTracker()
    payment_processor = PaymentProcessor()
    transaction_log = TransactionLog()

    seed_menu(menu_catalog)
    seed_drivers(delivery_tracker)

    print("=" * 50)
    print("        WELCOME TO PYBITE FOOD DELIVERY")
    print("=" * 50)

    customer = registration_flow(customer_manager)
    add_address_flow(customer, required=True)

    while True:
        header("MAIN MENU")
        print(f"Logged in as: {customer.name}")
        print("\n1. View Menu")
        print("2. Start a New Order")
        print("3. My Account")
        print("4. My Order History")
        print("5. Exit")
        choice = ask_choice("Choose an option", ["1", "2", "3", "4", "5"])

        if choice == "1":
            view_menu(menu_catalog)

        elif choice == "2":
            order = build_order_flow(order_manager, menu_catalog, customer)
            if order is None:
                continue
            method, result = checkout_flow(order, payment_processor)
            if method is None:
                print("\nYour order was placed but payment was not completed.")
                order.cancel()
                continue
            fulfillment_flow(order, delivery_tracker)
            receipt_flow(order, transaction_log, method, result)

        elif choice == "3":
            account_menu(customer)

        elif choice == "4":
            order_history_flow(transaction_log, customer)

        else:
            print("\nThanks for using PyBite Food Delivery. Goodbye!")
            break


if __name__ == "__main__":
    main()
