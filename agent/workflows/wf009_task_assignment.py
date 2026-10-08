from tools.data_tools import load_json_data


def run(request, context, steps, executor):
    """
    Execute WF009 - Employee Task Assignment.
    """

    task = context.get("task", request)

    required_skills = context.get(
        "required_skills",
        ["Java", "Python"]
    )

    priority = context.get(
        "priority",
        "Normal"
    )

    employees = executor._step(
        steps,
        "Load employee data",
        lambda: load_json_data("employees.json")
    )

    executor._step(
        steps,
        "Evaluate employee skills",
        lambda: True
    )

    required = {
        skill.lower()
        for skill in required_skills
    }

    suitable_employees = []

    for employee in employees:

        employee_skills = {
            skill.lower()
            for skill in employee.get(
                "skills",
                []
            )
        }

        if required.issubset(employee_skills):
            suitable_employees.append(employee)

    executor._step(
        steps,
        "Check employee workload",
        lambda: True
    )

    available = [
        employee
        for employee in suitable_employees
        if employee.get("workload", 100) < 100
    ]

    if not available:
        raise ValueError(
            "No suitable employee is available. "
            "Task should be escalated."
        )

    selected = min(
        available,
        key=lambda employee: employee.get(
            "workload",
            100
        )
    )

    executor._step(
        steps,
        "Assign task to best available employee",
        lambda: True
    )

    return {
        "task": task,
        "assigned_employee": selected.get("name"),
        "skills": selected.get("skills", []),
        "current_workload_percent": selected.get(
            "workload"
        ),
        "available_capacity_percent": (
            100 - selected.get(
                "workload",
                100
            )
        ),
        "priority": priority,
        "deadline": context.get("deadline")
    }