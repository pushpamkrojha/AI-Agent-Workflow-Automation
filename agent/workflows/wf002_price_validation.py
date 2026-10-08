from tools.common import read_csv, pct_difference


def run(request, context, steps, executor):
    """
    Execute WF002 - Product Price Validation.
    """

    products = executor._step(
        steps,
        "Load internal product prices",
        lambda: read_csv("products.csv")
    )

    vendor_prices = executor._step(
        steps,
        "Load vendor prices",
        lambda: read_csv("vendor_prices.csv")
    )

    merged = products.merge(
        vendor_prices,
        on="sku",
        suffixes=("_internal", "_vendor")
    )

    executor._step(
        steps,
        "Compare internal and vendor prices",
        lambda: True
    )

    merged["difference_percent"] = merged.apply(
        lambda row: pct_difference(
            row["internal_price"],
            row["vendor_price"]
        ),
        axis=1
    )

    merged["exception"] = (
        merged["difference_percent"] > 10
    )

    executor._step(
        steps,
        "Identify price exceptions above 10%",
        lambda: True
    )

    return {
        "threshold_percent": 10,
        "products": merged.to_dict(orient="records")
    }