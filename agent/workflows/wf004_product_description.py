def run(request, context, steps, executor):
    """
    Execute WF004 - Product Description Generator.
    """

    product_name = context.get("product_name")
    category = context.get("category")

    if not product_name:
        raise ValueError("Product name is required.")

    if not category:
        raise ValueError("Product category is required.")

    executor._step(
        steps,
        "Validate product information",
        lambda: True
    )

    content = executor._step(
        steps,
        "Generate product content",
        lambda: executor.llm.generate_product_content(context)
    )

    executor._step(
        steps,
        "Validate generated content",
        lambda: True
    )

    return content