from pathlib import Path

from tools.data_tools import read_table, normalize_columns


def run(request, context, steps, executor):
    """
    Execute WF003 - Vendor File Processing.
    """

    file_path = context.get("file_path")

    if not file_path:
        raise ValueError(
            "Vendor file path is required."
        )

    executor._step(
        steps,
        "Validate vendor file path",
        lambda: Path(file_path).exists()
    )

    data = executor._step(
        steps,
        "Read vendor file",
        lambda: read_table(file_path)
    )

    data = executor._step(
        steps,
        "Normalize column names",
        lambda: normalize_columns(data)
    )

    required_columns = {"sku", "product_name"}

    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    executor._step(
        steps,
        "Validate required columns",
        lambda: True
    )

    invalid_mask = (
        data["sku"].isna()
        | data["product_name"].isna()
        | (data["sku"].astype(str).str.strip() == "")
        | (data["product_name"].astype(str).str.strip() == "")
    )

    invalid_rows = data[invalid_mask].copy()
    cleaned_data = data[~invalid_mask].copy()

    executor._step(
        steps,
        "Identify invalid rows",
        lambda: True
    )

    executor._step(
        steps,
        "Create cleaned dataset",
        lambda: True
    )

    return {
        "cleaned_rows": cleaned_data.to_dict(orient="records"),
        "invalid_rows": invalid_rows.to_dict(orient="records"),
        "cleaned_count": len(cleaned_data),
        "invalid_count": len(invalid_rows)
    }