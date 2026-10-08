def run(request, context, steps, executor):
    """
    Execute WF007 - Marketing Campaign Brief.
    """

    goal = context.get("goal")
    dates = context.get("dates")

    if not goal:
        raise ValueError("Campaign goal is required.")

    if not dates:
        raise ValueError("Campaign dates are required.")

    executor._step(
        steps,
        "Validate campaign inputs",
        lambda: True
    )

    brief = executor._step(
        steps,
        "Generate campaign brief",
        lambda: executor.llm.campaign_brief(context)
    )

    executor._step(
        steps,
        "Validate campaign brief",
        lambda: True
    )

    return brief