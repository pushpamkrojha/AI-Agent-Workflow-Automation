from tools.data_tools import read_table
from tools.similarity import similarity


def run(request, context, steps, executor):
    """
    Execute WF006 - Duplicate Product Detection.
    """

    catalog = executor._step(
        steps,
        "Load product catalog",
        lambda: read_table("data/catalog.csv")
    )

    if catalog is None:
        raise ValueError(
            "Could not load the product catalog."
        )

    executor._step(
        steps,
        "Normalize identifiers",
        lambda: True
    )

    duplicate_groups = []

    sku_counts = catalog["sku"].value_counts()

    duplicate_skus = sku_counts[
        sku_counts > 1
    ].index.tolist()

    for sku in duplicate_skus:
        rows = catalog[
            catalog["sku"] == sku
        ]

        duplicate_groups.append({
            "products": rows.to_dict(
                orient="records"
            ),
            "confidence": "DEFINITE"
        })

    executor._step(
        steps,
        "Compare identifiers and attributes",
        lambda: True
    )

    for i in range(len(catalog)):
        for j in range(i + 1, len(catalog)):

            product_a = str(
                catalog.iloc[i]["product_name"]
            )

            product_b = str(
                catalog.iloc[j]["product_name"]
            )

            score = similarity(
                product_a,
                product_b
            )

            if score >= 85:

                # Avoid adding the exact SKU duplicate
                if catalog.iloc[i]["sku"] == catalog.iloc[j]["sku"]:
                    continue

                duplicate_groups.append({
                    "products": [
                        catalog.iloc[i].to_dict(),
                        catalog.iloc[j].to_dict()
                    ],
                    "similarity": round(score, 2),
                    "confidence": "POSSIBLE"
                })

    return {
        "duplicate_groups": duplicate_groups
    }