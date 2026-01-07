from typing import List
from openai import OpenAI
from backend.app.config import get_settings

INTENT_CATEGORIES: List[str] = [
    "financial_summary",
    "operational_status",
    "audit",
    "inventory",
    "hr_analytics",
    "sales_pipeline",
    "customer_support",
    "system_health",
    "unknown",
]

INTENT_PROMPT = """
You are an intent classifier for enterprise analytics queries.
Classify the user's request into one of the categories: {categories}.
Do NOT reference database schemas. Respond with the category only.
User question: "{question}"
"""


def detect_intent(question: str) -> str:
    settings = get_settings()
    if not settings.openai.api_key:
        return "unknown"
    client = OpenAI(api_key=settings.openai.api_key)
    prompt = INTENT_PROMPT.format(categories=", ".join(INTENT_CATEGORIES), question=question.strip())
    completion = client.chat.completions.create(
        model=settings.openai.model,
        messages=[
            {"role": "system", "content": "Return one category string only."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=8,
        temperature=0,
    )
    text = completion.choices[0].message.content.strip().lower()
    return text if text in INTENT_CATEGORIES else "unknown"
