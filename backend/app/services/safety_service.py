from typing import List


class SqlSafetyError(Exception):
    def __init__(self, issues: List[str]):
        self.issues = issues
        super().__init__("; ".join(issues))


def assert_sql_safe(sql: str) -> None:
    issues: List[str] = []
    lowered = sql.strip().lower()
    if not lowered.startswith("select"):
        issues.append("Only SELECT statements are allowed")
    forbidden = ["insert ", "update ", "delete ", "drop ", "alter ", "truncate ", "create "]
    if any(keyword in lowered for keyword in forbidden):
        issues.append("DDL/DML statements are blocked")
    if ";" in lowered[:-1]:
        issues.append("Multiple statements are blocked")
    if "information_schema" in lowered or "pg_catalog" in lowered:
        issues.append("System catalog access is blocked in compiled SQL")
    if issues:
        raise SqlSafetyError(issues)
