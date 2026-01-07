import json
from pathlib import Path
from backend.app.config import get_settings
from backend.app.models.audit import AuditRecord


def log_audit(record: AuditRecord) -> None:
    settings = get_settings()
    path = Path(settings.audit_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record.model_dump(), default=str) + "\n")


def explain_plan(plan: dict, sql: str | None = None) -> str:
    explanation = [
        f"Intent: {plan.get('intent')}",
        f"Fact table: {plan.get('fact_table')}",
        f"Dimensions: {', '.join(plan.get('dimensions', []))}",
        f"Metrics: {plan.get('metrics')}",
        f"Filters: {plan.get('filters')}",
        f"Group by: {plan.get('group_by')}",
    ]
    if sql:
        explanation.append(f"SQL: {sql}")
    return "\n".join(explanation)
