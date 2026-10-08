import json
import os
import re

from openai import OpenAI


class InputExtractor:

    def __init__(self):
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

    def extract(self, workflow, request):
        """
        Convert a natural-language request into
        structured workflow inputs.
        """

        if self.mock_mode:
            return self._mock_extract(
                workflow.workflow_id,
                request
            )

        prompt = f"""
You are an input extraction agent.

Workflow:
{workflow.name}

Required Inputs:
{workflow.inputs}

User Request:
{request}

Extract only information explicitly provided by the user.

Do NOT invent missing information.

Return only a JSON object containing
the available inputs.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": request
                }
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0
        )

        return json.loads(
            response.choices[0].message.content
        )

    def _mock_extract(self, workflow_id, request):

        text = request.lower()
        result = {}

        # =====================================================
        # WF004 - Product Description Generator
        # =====================================================

        if workflow_id == "WF004":

            if "wireless keyboard" in text:
                result["product_name"] = "Wireless Keyboard"

            if "electronics" in text:
                result["category"] = "Electronics"

            if "black" in text:
                result["color"] = "Black"

            if "bluetooth" in text:
                result["attributes"] = (
                    "Bluetooth connectivity"
                )

        # =====================================================
        # WF005 - Customer Order Status
        # =====================================================

        elif workflow_id == "WF005":

            match = re.search(
                r"\bORD-\d+\b",
                request,
                re.IGNORECASE
            )

            if match:
                result["order_id"] = (
                    match.group(0).upper()
                )

        # =====================================================
        # WF007 - Marketing Campaign Brief
        # =====================================================

        elif workflow_id == "WF007":

            result["goal"] = "Increase sales"
            result["audience"] = "Young customers"
            result["promotion"] = "Discount"
            result["dates"] = "June 1 to June 30"
            result["campaign"] = "Summer Sale"

        # =====================================================
        # WF009 - Employee Task Assignment
        # =====================================================

        elif workflow_id == "WF009":

            result["task"] = request
            result["required_skills"] = [
                "Java",
                "Python"
            ]
            result["priority"] = "Normal"

        # =====================================================
        # Return extracted data
        # =====================================================

        return result