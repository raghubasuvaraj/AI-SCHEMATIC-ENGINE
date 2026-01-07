"""
Plan service for generating Canonical Query Plans from natural language questions.
"""
import json
import re
from typing import Dict, List
from openai import OpenAI
from backend.app.config import get_settings
from backend.app.models.plan import CanonicalPlan
from backend.app.models.join import JoinGraph
from backend.app.models.mapping import MappingState
from backend.app.models.schema import SchemaSnapshot

PLAN_PROMPT = """
You are a SQL query planner. Your job is to convert a natural language question into a Canonical Query Plan JSON.

## Available Schema

**Fact Tables (main data tables):**
{fact_tables}

**Dimension Tables (lookup/reference tables):**
{dimension_tables}

**Available Columns by Table:**
{columns_by_table}

## Output Format (JSON)

```json
{{
  "intent": "REQUIRED: A short, human-readable title describing this query (NOT generic like 'aggregate_data' - use descriptive titles like 'Total bill amount per vendor', 'Pending invoices list', 'Bill count by status')",
  "fact_table": "string - the main table to query",
  "dimensions": ["array of dimension tables to join"],
  "metrics": [
    {{"column": "column_name", "aggregation": "count|sum|avg|min|max", "alias": "optional_alias"}}
  ],
  "filters": [
    {{"column": "column_name", "operator": "=|!=|>|<|>=|<=|in|between|like", "value": "filter_value"}}
  ],
  "group_by": ["columns to group by"],
  "order_by": ["columns to order by - use column names only, NO direction suffix"],
  "limit": 100
}}
```

## CRITICAL: Intent Field Rules
- The "intent" field MUST be a human-readable description of what the query does
- DO NOT use generic values like: "aggregate_data", "list_records", "filter_search"
- DO use descriptive titles like: "Total bills per vendor", "Pending invoice count", "Average payment by month"
- Think of intent as the TITLE for this query report
```

## IMPORTANT RULES FOR FILTERS

1. **EXTRACT ALL FILTER CONDITIONS** from the user's question:
   - "by tenant_id" → add filter: {{"column": "tenant_id", "operator": "=", "value": "?"}}
   - "by user_id" → add filter: {{"column": "user_id", "operator": "=", "value": "?"}}
   - "from last 30 days" → add filter: {{"column": "created_at", "operator": ">=", "value": "LAST_30_DAYS"}}
   - "where status is active" → add filter: {{"column": "status", "operator": "=", "value": "active"}}

2. **When user says "by X"**, it means they want to FILTER by that column. Add it as a filter.

3. **Date/Time filters:**
   - "last 30 days" → use operator ">=" with value "LAST_30_DAYS"
   - "this month" → use operator ">=" with value "THIS_MONTH"
   - "today" → use operator "=" with value "TODAY"

4. **Use "?" as placeholder** when the user doesn't specify an exact value but wants to filter by that column.

5. **Only use columns that exist** in the table's column list.

6. **MANDATORY: tenant_id filter** - ALWAYS include a tenant_id filter in EVERY query for security. This is non-negotiable.
   Add: {{"column": "tenant_id", "operator": "=", "value": "?"}} to filters.

7. **user_id is OPTIONAL** - Only add user_id filter when the user specifically mentions "my", "me", "user", etc.

## Examples

Question: "Show me all invoices from last week"
→ intent: "Invoices from last 7 days"
→ filters: [{{"column": "tenant_id", "operator": "=", "value": "?"}}, {{"column": "created_at", "operator": ">=", "value": "LAST_7_DAYS"}}]

Question: "List activity logs by user_id"
→ intent: "Activity logs filtered by user"
→ filters: [{{"column": "tenant_id", "operator": "=", "value": "?"}}, {{"column": "user_id", "operator": "=", "value": "?"}}]

Question: "Get total amount of bills per vendor"
→ intent: "Total bill amount per vendor"
→ metrics: [{{"column": "total_amount", "aggregation": "sum", "alias": "total_per_vendor"}}]
→ group_by: ["vendor_ref_id"]

Question: "Get orders where status is pending and amount > 1000"
→ intent: "Pending orders over 1000"
→ filters: [{{"column": "tenant_id", "operator": "=", "value": "?"}}, {{"column": "status", "operator": "=", "value": "pending"}}, {{"column": "amount", "operator": ">", "value": 1000}}]

Question: "Count of bills by status"
→ intent: "Bill count by status"
→ metrics: [{{"column": "bill_id", "aggregation": "count", "alias": "bill_count"}}]
→ group_by: ["status"]

---

User Question: "{question}"

Return ONLY the JSON object. No explanation.
"""


def build_plan(
    question: str,
    snapshot: SchemaSnapshot,
    mappings: MappingState,
    joins: JoinGraph,
) -> CanonicalPlan:
    settings = get_settings()
    if not settings.openai.api_key:
        raise ValueError("OPENAI_API_KEY not configured; cannot build plan.")

    # Build columns by table with data types for better context
    columns_by_table: Dict[str, List[str]] = {}
    for table in snapshot.tables:
        columns_by_table[table.name] = [
            f"{c.name} ({c.data_type})" for c in table.columns
        ]

    fact_tables = [t.table for t in mappings.tables if t.role == "fact"]
    dimension_tables = [t.table for t in mappings.tables if t.role == "dimension"]

    # If no mappings, use all tables as potential fact tables
    if not fact_tables:
        fact_tables = [t.name for t in snapshot.tables]
    
    client = OpenAI(api_key=settings.openai.api_key)
    prompt = PLAN_PROMPT.format(
        fact_tables=json.dumps(fact_tables, indent=2),
        dimension_tables=json.dumps(dimension_tables, indent=2) if dimension_tables else "[]",
        columns_by_table=json.dumps(columns_by_table, indent=2),
        question=question.strip(),
    )

    completion = client.chat.completions.create(
        model=settings.openai.model,
        messages=[
            {"role": "system", "content": "You are a SQL query planner. Return ONLY valid JSON. IMPORTANT: The 'intent' field must be a human-readable query title (like 'Total bills per vendor'), NOT generic terms like 'aggregate_data'."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,  # Slight temperature for more varied intent names
        max_tokens=800,
    )
    raw = completion.choices[0].message.content
    
    # Clean up the response - remove markdown code blocks if present
    raw = raw.strip()
    if raw.startswith("```"):
        # Remove markdown code block
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
    
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Planner did not return valid JSON: {raw[:200]}... Error: {e}")
    
    return CanonicalPlan.model_validate(data)
