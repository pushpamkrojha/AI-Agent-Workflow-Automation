from tools.data_tools import read_table


def run(request, context, steps, executor):
    """
    Execute WF008 - SEO Keyword Classification.
    """

    keywords = executor._step(
        steps,
        "Load SEO keywords",
        lambda: read_table("data/keywords.csv")
    )

    executor._step(
        steps,
        "Classify keyword search intent",
        lambda: True
    )

    def classify_intent(keyword):
        text = keyword.lower()

        if any(word in text for word in ["buy", "purchase", "order"]):
            return "transactional"

        if any(word in text for word in ["best", "review", "reviews"]):
            return "commercial"

        if any(word in text for word in ["what", "how", "guide"]):
            return "informational"

        return "navigational"

    def get_priority(intent):
        if intent in ["transactional", "commercial"]:
            return "high"

        if intent == "informational":
            return "medium"

        return "high"

    def get_page(intent):
        pages = {
            "informational": "blog/guide",
            "commercial": "category/comparison",
            "transactional": "product/landing",
            "navigational": "homepage/brand"
        }

        return pages[intent]

    results = []

    for _, row in keywords.iterrows():
        keyword = str(row["keyword"])
        intent = classify_intent(keyword)

        results.append({
            "keyword": keyword,
            "intent": intent,
            "priority": get_priority(intent),
            "recommended_page": get_page(intent)
        })

    executor._step(
        steps,
        "Assign keyword priority and recommended page",
        lambda: True
    )

    return results