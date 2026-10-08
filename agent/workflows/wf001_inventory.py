from tools.common import read_csv


def run(request, context, steps, executor):
    """
    Execute WF001 - Inventory Restock Check.

    This handler is kept outside executor.py so new workflows
    can be added as separate modules.
    """

    inventory = executor._step(
        steps,
        "Load inventory data",
        lambda: read_csv("inventory.csv")
    )

    threshold = float(context.get("minimum_stock", 10))

    low_stock = inventory[
        inventory["current_stock"] < threshold
    ].copy()

    executor._step(
        steps,
        "Compare current stock with minimum stock",
        lambda: True
    )

    executor._step(
        steps,
        "Identify products needing restock",
        lambda: True
    )

    low_stock["reorder_quantity"] = (
        threshold - low_stock["current_stock"]
    )

    executor._step(
        steps,
        "Calculate reorder quantity",
        lambda: True
    )

    return {
        "threshold": threshold,
        "products": low_stock.to_dict(orient="records")
    }