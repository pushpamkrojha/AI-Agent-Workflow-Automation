from tools.data_tools import load_json_data


def run(request, context, steps, executor):
    """
    Execute WF005 - Customer Order Status.
    """

    order_id = context.get("order_id")
    email = context.get("email")

    if not order_id and not email:
        raise ValueError(
            "Order ID or customer email is required."
        )

    orders = executor._step(
        steps,
        "Load order data",
        lambda: load_json_data("orders.json")
    )

    executor._step(
        steps,
        "Validate identifier",
        lambda: True
    )

    order = next(
        (
            order
            for order in orders
            if (
                order_id
                and order["order_id"] == order_id
            )
            or (
                email
                and order["email"].lower() == email.lower()
            )
        ),
        None
    )

    if not order:
        raise ValueError(
            "Order not found. Please provide another "
            "order ID or customer email."
        )

    executor._step(
        steps,
        "Search order",
        lambda: True
    )

    executor._step(
        steps,
        "Retrieve shipment information",
        lambda: True
    )

    return order