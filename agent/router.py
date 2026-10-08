import json
import os
import re

from openai import OpenAI


SELECT_TOOL = {
    "type": "function",
    "function": {
        "name": "select_workflow",
        "description": "Select exactly one workflow that best matches the user request.",
        "parameters": {
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow ID such as WF001"
                },
                "reason": {
                    "type": "string",
                    "description": "Short reason for the selection"
                }
            },
            "required": ["workflow_id", "reason"],
            "additionalProperties": False
        }
    }
}


class WorkflowRouter:

    def __init__(self, workflows):

        self.workflows = workflows

        self.mock_mode = (
            os.getenv("MOCK_MODE", "false").lower() == "true"
            or not os.getenv("OPENAI_API_KEY")
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-4o-mini"
        )

        self.client = (
            None
            if self.mock_mode
            else OpenAI()
        )


    def route(self, user_request: str):

        if self.mock_mode:
            return self._deterministic_route(
                user_request
            )

        catalog = self._build_workflow_catalog()

        system = (
            "You are the routing agent for a reusable "
            "business workflow engine. "
            "Select the single best workflow. "
            "Do not execute the workflow. "
            "Use only workflow IDs from the catalog.\n\n"
            + catalog
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system
                },
                {
                    "role": "user",
                    "content": user_request
                }
            ],
            tools=[SELECT_TOOL],
            tool_choice={
                "type": "function",
                "function": {
                    "name": "select_workflow"
                }
            },
            temperature=0
        )

        call = response.choices[0].message.tool_calls[0]

        args = json.loads(
            call.function.arguments
        )

        return (
            args["workflow_id"],
            args["reason"],
            "LLM tool calling"
        )


    def _build_workflow_catalog(self):

        return "\n".join(
            f"""
Workflow ID: {w.workflow_id}
Workflow Name: {w.name}
Trigger: {w.trigger}
Inputs: {w.inputs}
Steps: {w.steps}
Decision Logic: {w.decision_logic}
Expected Output: {w.expected_output}
""".strip()
            for w in self.workflows
        )


    def _deterministic_route(self, request):

        text = request.lower().strip()


        # -------------------------------------------------
        # Strong workflow-specific signals
        # -------------------------------------------------

        workflow_signals = {

            "WF001": [
                "restock",
                "restocking",
                "low stock",
                "inventory",
                "reorder",
                "reorder quantity"
            ],

            "WF002": [
                "price validation",
                "price difference",
                "price exception",
                "vendor price",
                "compare prices",
                "product prices"
            ],

            "WF003": [
                "vendor file",
                "vendor csv",
                "vendor xlsx",
                "vendor excel",
                "cleaned dataset",
                "invalid rows",
                "validate vendor"
            ],

            "WF004": [
                "product description",
                "product descriptions",
                "short description",
                "seo title",
                "meta description",
                "product content",
                "generate description"
            ],

            "WF005": [
                "order status",
                "where is my order",
                "track my order",
                "order tracking",
                "shipment status",
                "delivery status",
                "order id",
                "tracking"
            ],

            "WF006": [
                "duplicate product",
                "duplicate products",
                "similar products",
                "duplicate detection",
                "product similarity"
            ],

            "WF007": [
                "marketing campaign",
                "campaign brief",
                "campaign objective",
                "marketing brief",
                "promotion campaign"
            ],

            "WF008": [
                "seo keyword",
                "seo keywords",
                "search intent",
                "keyword classification",
                "keyword intent",
                "recommended page"
            ],

            "WF009": [
                "assign task",
                "task assignment",
                "employee assignment",
                "assign employee",
                "workload",
                "available employee"
            ],

            "WF010": [
                "performance report",
                "workflow performance",
                "failure rate",
                "execution time",
                "slow workflows",
                "workflow logs",
                "frequent errors"
            ]
        }


        # -------------------------------------------------
        # Score each workflow
        # -------------------------------------------------

        scores = {
            workflow_id: 0
            for workflow_id in workflow_signals
        }


        for workflow_id, signals in workflow_signals.items():

            for signal in signals:

                if signal in text:

                    # Longer phrases are stronger evidence.
                    scores[workflow_id] += (
                        3
                        if len(signal.split()) > 1
                        else 1
                    )


        # -------------------------------------------------
        # Select strongest match
        # -------------------------------------------------

        best_workflow = max(
            scores,
            key=scores.get
        )

        best_score = scores[best_workflow]


        if best_score == 0:

            return self._metadata_fallback(
                request
            )


        reason = (
            f"Matched strong workflow signals "
            f"for {best_workflow}."
        )

        return (
            best_workflow,
            reason,
            "Deterministic fallback"
        )


    def _metadata_fallback(self, request):

        request_words = set(
            re.findall(
                r"[a-zA-Z0-9]+",
                request.lower()
            )
        )

        best_workflow = None
        best_score = 0


        for workflow in self.workflows:

            metadata = " ".join([
                workflow.name,
                workflow.trigger,
                workflow.inputs,
                workflow.steps,
                workflow.decision_logic,
                workflow.expected_output
            ]).lower()


            metadata_words = set(
                re.findall(
                    r"[a-zA-Z0-9]+",
                    metadata
                )
            )


            score = len(
                request_words
                & metadata_words
            )


            if score > best_score:

                best_score = score
                best_workflow = workflow


        if (
            best_workflow is None
            or best_score == 0
        ):

            raise ValueError(
                "I could not identify a matching workflow. "
                "Please describe the business request more clearly."
            )


        reason = (
            "Matched the request with workflow metadata "
            f"for {best_workflow.name}."
        )


        return (
            best_workflow.workflow_id,
            reason,
            "Metadata fallback"
        )