from dataclasses import dataclass
from typing import Any


@dataclass
class Workflow:
    workflow_id: str
    name: str
    trigger: str
    inputs: str
    steps: str
    decision_logic: str
    tools_required: str
    expected_output: str


@dataclass
class AgentResult:
    workflow_id: str
    workflow_name: str
    status: str
    steps: list[dict[str, Any]]
    result: Any
    error: str | None = None