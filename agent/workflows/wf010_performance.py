from tools.data_tools import read_table


def run(request, context, steps, executor):
    """
    Execute WF010 - Workflow Performance Report.
    """

    logs = executor._step(
        steps,
        "Load workflow execution logs",
        lambda: read_table("data/execution_logs.csv")
    )

    executor._step(
        steps,
        "Calculate workflow performance metrics",
        lambda: True
    )

    report = []

    for workflow_id, group in logs.groupby("workflow_id"):

        total = len(group)

        failures = (
            group["status"]
            .astype(str)
            .str.upper()
            .eq("FAILED")
            .sum()
        )

        failure_rate = (
            failures / total * 100
            if total
            else 0
        )

        average_execution_time = (
            group["execution_ms"].mean()
            if total
            else 0
        )

        frequent_errors = {}

        if "error" in group.columns:
            errors = (
                group["error"]
                .dropna()
                .astype(str)
            )

            frequent_errors = (
                errors.value_counts()
                .head(3)
                .to_dict()
            )

        slow = bool(average_execution_time > 1000)

        flag = bool(
            failure_rate > 10
            or slow
        )

        report.append({ 
            "workflow_id": workflow_id,
            "total_executions": total,
            "failures": int(failures),
            "failure_rate_percent": round(
                failure_rate,
                2
            ),
            "average_execution_time_ms": round(
                average_execution_time,
                2
            ),
            "frequent_errors": frequent_errors,
            "slow_workflow": slow,
            "flag": flag
        })

    executor._step(
        steps,
        "Identify frequent errors and slow workflows",
        lambda: True
    )

    return report