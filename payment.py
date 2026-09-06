def checkout_flow(
    order: Order, payment_processor: PaymentProcessor
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
