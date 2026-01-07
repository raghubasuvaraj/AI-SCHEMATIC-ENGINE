"""
Service to generate sample questions based on the database schema and actual data.
Analyzes real data values to provide context-aware question suggestions.
"""
import json
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from openai import OpenAI
from backend.app.config import get_settings
from backend.app.services.schema_service import load_cached_schema, introspect_schema
from backend.app.utils.db import get_engine


def analyze_table_data(table_name: str, columns: List[str], limit: int = 100) -> Dict[str, Any]:
    """Analyze actual data from a table to understand its content."""
    engine = get_engine()
    settings = get_settings()
    analysis = {
        "table": table_name,
        "row_count": 0,
        "sample_values": {},
        "distinct_values": {},
        "date_range": {},
        "numeric_stats": {},
    }
    
    try:
        with engine.connect() as conn:
            # Get row count
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            analysis["row_count"] = result.scalar() or 0
            
            # Analyze each column for sample values
            for col in columns[:10]:  # Limit columns analyzed
                col_lower = col.lower()
                
                # Get distinct values for enum-like columns
                if any(kw in col_lower for kw in ['status', 'type', 'category', 'state', 'code', 'flag']):
                    try:
                        result = conn.execute(text(f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 20"))
                        values = [str(row[0]) for row in result.fetchall() if row[0]]
                        if values and len(values) <= 20:
                            analysis["distinct_values"][col] = values
                    except:
                        pass
                
                # Get date range for date columns
                elif any(kw in col_lower for kw in ['date', 'created', 'updated', 'time', '_at']):
                    try:
                        result = conn.execute(text(f"SELECT MIN({col}), MAX({col}) FROM {table_name} WHERE {col} IS NOT NULL"))
                        row = result.fetchone()
                        if row and row[0]:
                            analysis["date_range"][col] = {"min": str(row[0]), "max": str(row[1])}
                    except:
                        pass
                
                # Get numeric stats for amount/value columns
                elif any(kw in col_lower for kw in ['amount', 'total', 'price', 'cost', 'value', 'qty', 'quantity', 'count']):
                    try:
                        result = conn.execute(text(f"SELECT MIN({col}), MAX({col}), AVG({col}) FROM {table_name} WHERE {col} IS NOT NULL"))
                        row = result.fetchone()
                        if row and row[0] is not None:
                            analysis["numeric_stats"][col] = {
                                "min": float(row[0]) if row[0] else 0,
                                "max": float(row[1]) if row[1] else 0,
                                "avg": round(float(row[2]), 2) if row[2] else 0
                            }
                    except:
                        pass
                
                # Get sample values for name/description columns
                elif any(kw in col_lower for kw in ['name', 'title', 'description', 'vendor', 'customer']):
                    try:
                        result = conn.execute(text(f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 5"))
                        values = [str(row[0]) for row in result.fetchall() if row[0]]
                        if values:
                            analysis["sample_values"][col] = values
                    except:
                        pass
    except Exception as e:
        analysis["error"] = str(e)
    
    return analysis


def generate_data_aware_questions() -> List[Dict[str, Any]]:
    """Generate questions based on actual database analysis."""
    settings = get_settings()
    questions = []
    
    try:
        snapshot = load_cached_schema()
        if not snapshot:
            snapshot = introspect_schema()
        
        # Analyze key tables
        table_analyses = []
        for table in snapshot.tables[:10]:  # Analyze top 10 tables
            columns = [c.name for c in table.columns]
            analysis = analyze_table_data(table.name, columns)
            if analysis["row_count"] > 0:
                table_analyses.append(analysis)
        
        # Generate questions based on analysis
        for analysis in table_analyses:
            table_name = analysis["table"]
            row_count = analysis["row_count"]
            
            # Base table query
            questions.append({
                "category": "Data Exploration",
                "question": f"Show me all records from {table_name}",
                "requires_tenant": True,
                "requires_user": False,
                "data_hint": f"Table has {row_count:,} rows"
            })
            
            # Status-based questions
            for col, values in analysis["distinct_values"].items():
                if values:
                    for val in values[:3]:  # First 3 distinct values
                        questions.append({
                            "category": "Filtering",
                            "question": f"Show me {table_name} where {col} is '{val}'",
                            "requires_tenant": True,
                            "requires_user": False,
                            "data_hint": f"Available values: {', '.join(values[:5])}"
                        })
                    # Count by status
                    questions.append({
                        "category": "Aggregation",
                        "question": f"Count {table_name} by {col}",
                        "requires_tenant": True,
                        "requires_user": False,
                        "data_hint": f"Groups: {', '.join(values)}"
                    })
            
            # Date-based questions
            for col, date_range in analysis["date_range"].items():
                questions.append({
                    "category": "Time-based",
                    "question": f"Show me {table_name} from last 30 days",
                    "requires_tenant": True,
                    "requires_user": False,
                    "data_hint": f"Date range: {date_range['min']} to {date_range['max']}"
                })
                questions.append({
                    "category": "Time-based",
                    "question": f"Show me {table_name} created this month",
                    "requires_tenant": True,
                    "requires_user": False,
                    "data_hint": f"Date column: {col}"
                })
            
            # Numeric aggregations
            for col, stats in analysis["numeric_stats"].items():
                questions.append({
                    "category": "Aggregation",
                    "question": f"What is the total {col} in {table_name}?",
                    "requires_tenant": True,
                    "requires_user": False,
                    "data_hint": f"Range: {stats['min']:,.2f} - {stats['max']:,.2f}, Avg: {stats['avg']:,.2f}"
                })
                questions.append({
                    "category": "Aggregation",
                    "question": f"What is the average {col} in {table_name}?",
                    "requires_tenant": True,
                    "requires_user": False,
                    "data_hint": f"Current avg: {stats['avg']:,.2f}"
                })
                # Top records
                questions.append({
                    "category": "Top Records",
                    "question": f"Show top 10 {table_name} by {col}",
                    "requires_tenant": True,
                    "requires_user": False,
                    "data_hint": f"Max value: {stats['max']:,.2f}"
                })
                # Filter by amount
                if stats['avg'] > 0:
                    threshold = round(stats['avg'] * 2, 2)
                    questions.append({
                        "category": "Filtering",
                        "question": f"Show {table_name} where {col} is greater than {threshold}",
                        "requires_tenant": True,
                        "requires_user": False,
                        "data_hint": f"Threshold is ~2x average"
                    })
            
            # Sample value questions
            for col, values in analysis["sample_values"].items():
                if values:
                    val = values[0]
                    questions.append({
                        "category": "Search",
                        "question": f"Find {table_name} where {col} contains '{val[:20]}'",
                        "requires_tenant": True,
                        "requires_user": False,
                        "data_hint": f"Sample value: {val}"
                    })
        
    except Exception as e:
        questions.append({
            "category": "Error",
            "question": f"Error analyzing database: {str(e)}",
            "requires_tenant": False,
            "requires_user": False,
            "data_hint": "Please check database connection"
        })
    
    return questions


# Pre-defined sample questions based on common AP (Accounts Payable) patterns
SAMPLE_QUESTIONS = [
    # Bill Management Questions
    {"category": "Bills", "question": "Show me my total bill amount for this month", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "What is my total bill amount for last month?", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "List all pending bills for my tenant", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "Show bills with amount greater than $10,000", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "How many bills are overdue?", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "Show me bills created in the last 7 days", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "What is the average bill amount this quarter?", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "List all bills waiting for approval", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "Show me the top 10 highest value bills", "requires_tenant": True, "requires_user": False},
    {"category": "Bills", "question": "How many bills were approved this week?", "requires_tenant": True, "requires_user": False},
    
    # Vendor Questions
    {"category": "Vendors", "question": "List all active vendors", "requires_tenant": True, "requires_user": False},
    {"category": "Vendors", "question": "Show me vendor details with outstanding payments", "requires_tenant": True, "requires_user": False},
    {"category": "Vendors", "question": "How many vendors do we have in total?", "requires_tenant": True, "requires_user": False},
    {"category": "Vendors", "question": "List vendors added in the last 30 days", "requires_tenant": True, "requires_user": False},
    
    # Payment Questions
    {"category": "Payments", "question": "Show me all payments made this month", "requires_tenant": True, "requires_user": False},
    {"category": "Payments", "question": "What is the total payment amount for last quarter?", "requires_tenant": True, "requires_user": False},
    {"category": "Payments", "question": "List pending payments", "requires_tenant": True, "requires_user": False},
    
    # Activity Questions
    {"category": "Activity", "question": "Show my recent activity log", "requires_tenant": True, "requires_user": True},
    {"category": "Activity", "question": "List all actions performed by me today", "requires_tenant": True, "requires_user": True},
    {"category": "Activity", "question": "Show audit trail for bill approvals", "requires_tenant": True, "requires_user": False},
]


def get_sample_questions() -> List[Dict[str, Any]]:
    """Return pre-defined sample questions."""
    return SAMPLE_QUESTIONS


def generate_ai_questions(count: int = 10) -> List[Dict[str, Any]]:
    """Generate additional questions using AI based on the schema and data analysis."""
    settings = get_settings()
    if not settings.openai.api_key:
        return []
    
    snapshot = load_cached_schema() or introspect_schema()
    
    # Analyze actual data for better context
    data_context = []
    for table in snapshot.tables[:8]:
        columns = [c.name for c in table.columns]
        analysis = analyze_table_data(table.name, columns)
        if analysis["row_count"] > 0:
            context = f"- {table.name} ({analysis['row_count']:,} rows)"
            if analysis["distinct_values"]:
                for col, vals in list(analysis["distinct_values"].items())[:2]:
                    context += f"\n  - {col}: {', '.join(vals[:5])}"
            if analysis["numeric_stats"]:
                for col, stats in list(analysis["numeric_stats"].items())[:2]:
                    context += f"\n  - {col}: min={stats['min']:,.0f}, max={stats['max']:,.0f}, avg={stats['avg']:,.0f}"
            data_context.append(context)
    
    prompt = f"""Based on this database with REAL DATA, generate {count} practical business questions.

Database Analysis:
{chr(10).join(data_context)}

Rules:
1. Generate questions that will return REAL DATA from this database
2. Use actual column names and realistic filter values based on the data shown
3. All questions require tenant_id filter (mandatory for security)
4. Include mix of: list queries, aggregations (sum, count, avg), filters, date ranges
5. Make questions practical for business users

Return as JSON array:
[
  {{"category": "...", "question": "...", "requires_tenant": true, "requires_user": false, "data_hint": "..."}},
  ...
]

Return ONLY the JSON array."""

    client = OpenAI(api_key=settings.openai.api_key)
    completion = client.chat.completions.create(
        model=settings.openai.model,
        messages=[
            {"role": "system", "content": "You are an expert at generating practical database queries."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )
    
    raw = completion.choices[0].message.content.strip()
    # Clean up markdown if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "questions" in result:
            return result["questions"]
        else:
            return []
    except json.JSONDecodeError:
        return []


def get_all_questions(include_ai: bool = False, include_data_analysis: bool = True, ai_count: int = 10) -> Dict[str, Any]:
    """Get all sample questions, optionally with AI-generated and data-aware ones."""
    questions = get_sample_questions()
    
    # Add data-aware questions based on actual database content
    if include_data_analysis:
        try:
            data_questions = generate_data_aware_questions()
            questions = questions + data_questions
        except Exception:
            pass
    
    if include_ai:
        ai_questions = generate_ai_questions(ai_count)
        questions = questions + ai_questions
    
    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for q in questions:
        cat = q.get("category", "Other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(q)
    
    return {
        "total": len(questions),
        "categories": list(by_category.keys()),
        "questions": questions,
        "by_category": by_category,
    }


def export_questions_to_text(questions: List[Dict[str, Any]]) -> str:
    """Export questions as formatted text."""
    lines = ["# Sample Questions for AP Query Engine\n"]
    lines.append("Note: All queries require tenant_id for security.\n")
    lines.append("Questions marked with [USER] also require user_id.\n\n")
    
    # Group by category
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for q in questions:
        cat = q.get("category", "Other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(q)
    
    for category, qs in by_category.items():
        lines.append(f"## {category}\n")
        for i, q in enumerate(qs, 1):
            user_tag = " [USER]" if q.get("requires_user") else ""
            hint = f" — {q['data_hint']}" if q.get("data_hint") else ""
            lines.append(f"{i}. {q['question']}{user_tag}{hint}\n")
        lines.append("\n")
    
    return "".join(lines)
