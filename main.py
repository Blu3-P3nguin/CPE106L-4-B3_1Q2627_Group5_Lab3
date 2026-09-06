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
