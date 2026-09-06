def receipt_flow(
    order: Order,
    transaction_log: TransactionLog,
    method: PaymentMethod,
    result: PaymentResult,
) -> None:
    header("RECEIPT")
    record = transaction_log.record_transaction(
        order, method.method_name, result.transaction_id
    )
    print(record.to_receipt())


def order_history_flow(transaction_log: TransactionLog, customer: Customer) -> None:
    header("MY ORDER HISTORY")
    records = transaction_log.get_history_by_customer(customer.customer_id)
    if not records:
        print("You haven't completed any orders yet.")
        return
    for i, record in enumerate(records):
        print(
            f"{i + 1}. {record.timestamp.strftime('%Y-%m-%d %H:%M')} - "
            f"Order {record.order_id} - ${record.total:.2f}"
        )
    choice = ask(
        "\nEnter a number to view the full receipt, or press Enter to go back: "
    )
    if choice.isdigit() and 1 <= int(choice) <= len(records):
        print()
        print(records[int(choice) - 1].to_receipt())
