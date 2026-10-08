import os
from openai import OpenAI

class LLMTools:
    def __init__(self):
        self.mock = os.getenv("MOCK_MODE", "false").lower() == "true" or not os.getenv("OPENAI_API_KEY")
        self.client = None if self.mock else OpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate_product_content(self, data):
        missing = [k for k in ["material", "color", "target_audience"] if not data.get(k)]
        if self.mock:
            name = data.get("product_name", "Unnamed Product")
            category = data.get("category", "product")
            miss = ", ".join(missing) if missing else "none"
            return {
                "product_description": f"{name} is a {category} designed for the stated product use. Missing attributes: {miss}.",
                "short_description": f"{name} — {category}. Missing attributes: {miss}.",
                "seo_title": f"{name} | {category}",
                "meta_description": f"Explore {name}, a {category}. Missing attributes: {miss}.",
            }
        prompt = f"Generate product content from ONLY these facts. Never invent missing attributes. Data: {data}. Return JSON with product_description, short_description, seo_title, meta_description. Explicitly mention missing information where applicable."
        r = self.client.chat.completions.create(model=self.model, messages=[{"role":"user","content":prompt}], temperature=0.3)
        import json
        return json.loads(r.choices[0].message.content)

    def campaign_brief(self, data):
        if self.mock:
            products = data.get("products") or []
            promotion = data.get("promotion") or "the stated promotion"
            audience = data.get("audience") or "the target audience"

            if products:
                product_text = ", ".join(products)
                messaging = (
                    f"Promote {product_text} to {audience} "
                    f"using {promotion}."
                )
            else:
                messaging = (
                    f"Promote the campaign to {audience} "
                    f"using {promotion}."
                )

            return {
                "objective": data["goal"],
                "audience": data.get("audience"),
                "messaging": messaging,
                "channels": ["Email", "Social Media", "Website"],
                "timeline": data["dates"],
                "checklist": [
                    "Approve creative",
                    "Prepare landing page",
                    "Schedule campaign",
                    "Measure results"
                ]
            }

        prompt = (
            f"Create a structured marketing campaign brief "
            f"using only these facts: {data}. "
            f"Return JSON keys objective,audience,messaging,"
            f"channels,timeline,checklist."
        )

        r = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4
        )

        import json
        return json.loads(r.choices[0].message.content)
