"""
Schema routes for database introspection and documentation generation.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI
from backend.app.services.schema_service import introspect_schema, load_cached_schema
from backend.app.services.mapping_service import get_mapping_state
from backend.app.services.join_service import get_join_graph
from backend.app.config import get_settings

router = APIRouter(prefix="/schema", tags=["schema"])


# ===== Models for Table Documentation =====

class ColumnDocumentation(BaseModel):
    name: str
    data_type: str
    possible_values: Optional[str] = None
    description: Optional[str] = None
    is_primary: bool = False
    is_foreign: bool = False


class TableDocumentation(BaseModel):
    table_name: str
    purpose: str
    columns: List[ColumnDocumentation]
    frequent_queries: List[str]
    join_columns: List[Dict[str, str]]
    role: Optional[str] = None  # fact or dimension
    row_count_estimate: Optional[str] = None


class SchemaDocumentation(BaseModel):
    database: str
    dialect: str
    tables: List[TableDocumentation]
    generated_at: str


# ===== Endpoints =====

@router.get("", summary="Introspect database schema (metadata only)")
def get_schema():
    settings = get_settings()
    if not settings.db.database:
        raise HTTPException(
            status_code=500,
            detail="Database not configured. Please set DB_NAME in .env file."
        )
    try:
        return introspect_schema()
    except Exception as exc:
        raise HTTPException(
            status_code=500, 
            detail=f"Database connection error: {str(exc)}. Check your .env configuration."
        )


@router.get("/cached", summary="Return last cached schema snapshot")
def get_cached_schema():
    cached = load_cached_schema()
    if not cached:
        raise HTTPException(status_code=404, detail="No cached schema available")
    return cached


@router.get("/documentation", summary="Generate table documentation")
def generate_documentation():
    """
    Generate comprehensive table documentation in the format:
    - Table name - purpose
    - Column name - possible values
    - Frequent queries on tables
    - Join columns to use
    """
    from datetime import datetime
    
    snapshot = load_cached_schema() or introspect_schema()
    mappings = get_mapping_state()
    joins = get_join_graph()
    settings = get_settings()
    
    # Build mapping lookup
    table_roles = {t.table: t.role for t in mappings.tables}
    table_meanings = {t.table: t.business_name for t in mappings.tables}
    column_meanings = {(c.table, c.column): c.business_meaning for c in mappings.columns}
    
    # Build join lookup
    table_joins = {}
    for join in joins.joins:
        if join.approved:
            if join.left_table not in table_joins:
                table_joins[join.left_table] = []
            if join.right_table not in table_joins:
                table_joins[join.right_table] = []
            
            table_joins[join.left_table].append({
                "column": join.left_column,
                "joins_to": f"{join.right_table}.{join.right_column}",
                "type": join.join_type or "LEFT JOIN"
            })
            table_joins[join.right_table].append({
                "column": join.right_column,
                "joins_to": f"{join.left_table}.{join.left_column}",
                "type": join.join_type or "LEFT JOIN"
            })
    
    # Build enum lookup
    enum_values = {}
    for enum in snapshot.enums:
        enum_values[(enum.table, enum.column)] = enum.values
    
    # Generate documentation for each table
    tables_doc = []
    for table in snapshot.tables:
        # Get columns documentation
        columns_doc = []
        for col in table.columns:
            possible_vals = None
            
            # Check for enum values
            if (table.name, col.name) in enum_values:
                possible_vals = ", ".join(enum_values[(table.name, col.name)][:10])
                if len(enum_values[(table.name, col.name)]) > 10:
                    possible_vals += "..."
            
            # Get business meaning if available
            description = column_meanings.get((table.name, col.name), col.comment or None)
            
            columns_doc.append(ColumnDocumentation(
                name=col.name,
                data_type=col.data_type,
                possible_values=possible_vals,
                description=description,
                is_primary=col.is_primary,
                is_foreign=col.is_foreign,
            ))
        
        # Generate purpose (use business name if available)
        purpose = table_meanings.get(table.name, table.comment or f"Table for storing {table.name.replace('_', ' ')} data")
        
        # Get role
        role = table_roles.get(table.name)
        
        # Get join columns
        join_cols = table_joins.get(table.name, [])
        
        # Generate frequent queries based on table structure
        frequent_queries = _generate_frequent_queries(table, role)
        
        tables_doc.append(TableDocumentation(
            table_name=table.name,
            purpose=purpose,
            columns=columns_doc,
            frequent_queries=frequent_queries,
            join_columns=join_cols,
            role=role,
        ))
    
    return SchemaDocumentation(
        database=settings.db.database,
        dialect=settings.db.dialect,
        tables=tables_doc,
        generated_at=datetime.utcnow().isoformat(),
    )


@router.post("/documentation/generate-ai", summary="Generate AI-powered table documentation")
def generate_ai_documentation(payload: dict):
    """
    Use LLM to generate intelligent table documentation including:
    - Inferred purpose
    - Possible values analysis
    - Suggested frequent queries
    - Join recommendations
    """
    table_name = payload.get("table_name")
    
    snapshot = load_cached_schema() or introspect_schema()
    settings = get_settings()
    
    if not settings.openai.api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    
    # Find the specific table
    table = None
    for t in snapshot.tables:
        if t.name == table_name:
            table = t
            break
    
    if not table:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    
    # Prepare column info for LLM
    columns_info = []
    for col in table.columns:
        col_info = f"- {col.name} ({col.data_type})"
        if col.is_primary:
            col_info += " [PRIMARY KEY]"
        if col.is_foreign:
            col_info += f" [FOREIGN KEY -> {col.foreign_key.ref_table}.{col.foreign_key.ref_column}]" if col.foreign_key else " [FOREIGN KEY]"
        columns_info.append(col_info)
    
    prompt = f"""Analyze this database table and provide documentation:

Table: {table.name}
Columns:
{chr(10).join(columns_info)}

Provide a JSON response with:
1. "purpose": A clear description of what this table stores (1-2 sentences)
2. "column_descriptions": An object mapping column names to their likely purpose/meaning
3. "frequent_queries": An array of 3-5 common queries users might run on this table (in natural language)
4. "join_recommendations": An array of recommended join patterns based on column names

Return ONLY valid JSON, no markdown."""

    try:
        client = OpenAI(api_key=settings.openai.api_key)
        completion = client.chat.completions.create(
            model=settings.openai.model,
            messages=[
                {"role": "system", "content": "You are a database documentation expert. Analyze tables and provide clear, useful documentation. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        
        import json
        response_text = completion.choices[0].message.content.strip()
        # Try to parse as JSON
        try:
            ai_doc = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                ai_doc = json.loads(json_match.group())
            else:
                ai_doc = {"raw_response": response_text}
        
        return {
            "table_name": table_name,
            "documentation": ai_doc,
            "columns": [{"name": c.name, "type": c.data_type} for c in table.columns],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI documentation failed: {str(exc)}")


@router.get("/export", summary="Export schema documentation as formatted text")
def export_documentation():
    """Export table documentation in a readable text format."""
    doc = generate_documentation()
    
    lines = []
    lines.append(f"# Database Documentation: {doc.database}")
    lines.append(f"Dialect: {doc.dialect}")
    lines.append(f"Generated: {doc.generated_at}")
    lines.append("")
    lines.append("=" * 80)
    
    for i, table in enumerate(doc.tables, 1):
        lines.append("")
        lines.append(f"## Table {i}: {table.table_name}")
        if table.role:
            lines.append(f"Role: {table.role.upper()}")
        lines.append("")
        lines.append(f"**Purpose:** {table.purpose}")
        lines.append("")
        
        # Columns
        lines.append("### Columns:")
        for col in table.columns:
            pk_fk = ""
            if col.is_primary:
                pk_fk = " [PK]"
            if col.is_foreign:
                pk_fk += " [FK]"
            
            line = f"  - {col.name} ({col.data_type}){pk_fk}"
            if col.possible_values:
                line += f"\n    Possible values: {col.possible_values}"
            if col.description:
                line += f"\n    Description: {col.description}"
            lines.append(line)
        
        # Frequent queries
        if table.frequent_queries:
            lines.append("")
            lines.append("### Frequent Queries:")
            for q in table.frequent_queries:
                lines.append(f"  - {q}")
        
        # Join columns
        if table.join_columns:
            lines.append("")
            lines.append("### Join Columns:")
            for j in table.join_columns:
                lines.append(f"  - {j['column']} → {j['joins_to']} ({j.get('type', 'JOIN')})")
        
        lines.append("")
        lines.append("-" * 80)
    
    return {
        "format": "text",
        "content": "\n".join(lines),
        "table_count": len(doc.tables),
    }


def _generate_frequent_queries(table, role: str = None) -> List[str]:
    """Generate common query patterns based on table structure."""
    queries = []
    
    # Find key columns
    pk_cols = [c.name for c in table.columns if c.is_primary]
    fk_cols = [c.name for c in table.columns if c.is_foreign]
    date_cols = [c.name for c in table.columns if any(d in c.data_type.lower() for d in ['date', 'time', 'timestamp'])]
    amount_cols = [c.name for c in table.columns if any(d in c.data_type.lower() for d in ['decimal', 'money', 'numeric', 'float', 'double']) or any(w in c.name.lower() for w in ['amount', 'total', 'price', 'cost', 'value'])]
    status_cols = [c.name for c in table.columns if 'status' in c.name.lower() or 'state' in c.name.lower() or 'type' in c.name.lower()]
    
    table_friendly = table.name.replace('_', ' ')
    
    # Generate queries based on column types
    if role == "fact" or amount_cols:
        if amount_cols and date_cols:
            queries.append(f"Get total {amount_cols[0]} by month from {table_friendly}")
        if amount_cols:
            queries.append(f"Show sum of {amount_cols[0]} grouped by category")
    
    if date_cols:
        queries.append(f"List {table_friendly} from last 30 days")
    
    if status_cols:
        queries.append(f"Count {table_friendly} by {status_cols[0]}")
    
    if pk_cols:
        queries.append(f"Find specific {table_friendly} by {pk_cols[0]}")
    
    if fk_cols:
        queries.append(f"Get {table_friendly} with related {fk_cols[0].replace('_id', '')} details")
    
    # Default query
    if not queries:
        queries.append(f"List all {table_friendly}")
        queries.append(f"Count total {table_friendly}")
    
    return queries[:5]  # Return max 5 queries
