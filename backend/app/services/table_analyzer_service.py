"""
Service for automatically analyzing tables and classifying them as fact or dimension tables.
Uses heuristics based on:
- Table naming conventions
- Column analysis (presence of foreign keys, numeric columns, date columns)
- Row counts (fact tables typically have more rows)
"""
from typing import Dict, List, Any, Tuple
from sqlalchemy import text
from backend.app.models.schema import SchemaSnapshot, Table
from backend.app.models.mapping import TableMapping, MappingState
from backend.app.services.mapping_service import save_mapping_state, get_mapping_state
from backend.app.utils.db import get_engine
from backend.app.config import get_settings

# Common naming patterns for dimension/master tables
DIMENSION_PATTERNS = [
    "master", "dim_", "_dim", "dimension", "lookup", "ref_", "_ref",
    "type", "status", "category", "config", "setting", "param",
    "country", "state", "city", "currency", "unit", "vendor", "customer",
    "user", "role", "permission", "department", "employee"
]

# Common naming patterns for fact tables
FACT_PATTERNS = [
    "fact_", "_fact", "transaction", "log", "history", "event",
    "order", "sale", "purchase", "invoice", "bill", "payment",
    "activity", "audit", "record", "entry", "detail", "line"
]


def analyze_table_type(table: Table, row_count: int = 0) -> Tuple[str, float, str]:
    """
    Analyze a table and determine if it's a fact or dimension table.
    Returns: (role, confidence, reason)
    """
    name_lower = table.name.lower()
    
    # Check for dimension patterns in name
    for pattern in DIMENSION_PATTERNS:
        if pattern in name_lower:
            return ("dimension", 0.8, f"Name contains '{pattern}' pattern")
    
    # Check for fact patterns in name
    for pattern in FACT_PATTERNS:
        if pattern in name_lower:
            return ("fact", 0.8, f"Name contains '{pattern}' pattern")
    
    # Analyze columns
    pk_count = sum(1 for c in table.columns if c.is_primary)
    fk_count = sum(1 for c in table.columns if c.is_foreign)
    numeric_cols = sum(1 for c in table.columns if c.data_type.lower() in 
                       ['int', 'integer', 'bigint', 'decimal', 'numeric', 'float', 'double', 'money'])
    date_cols = sum(1 for c in table.columns if c.data_type.lower() in 
                    ['date', 'datetime', 'timestamp', 'time'])
    total_cols = len(table.columns)
    
    # Fact table indicators:
    # - Many foreign keys (joins to dimension tables)
    # - Date/timestamp columns (for time-series analysis)
    # - Numeric columns for metrics/measures
    # - Higher row counts
    
    fact_score = 0
    dim_score = 0
    reasons = []
    
    # Foreign key ratio
    if total_cols > 0:
        fk_ratio = fk_count / total_cols
        if fk_ratio > 0.3:
            fact_score += 2
            reasons.append(f"High FK ratio ({fk_ratio:.1%})")
        elif fk_ratio < 0.1 and fk_count <= 1:
            dim_score += 1
            reasons.append("Low FK count")
    
    # Date columns
    if date_cols >= 2:
        fact_score += 2
        reasons.append(f"Multiple date columns ({date_cols})")
    elif date_cols == 0:
        dim_score += 1
        reasons.append("No date columns")
    
    # Numeric columns (potential measures)
    if numeric_cols >= 3:
        fact_score += 1
        reasons.append(f"Multiple numeric columns ({numeric_cols})")
    
    # Column count (dimension tables tend to have fewer columns)
    if total_cols <= 10:
        dim_score += 1
        reasons.append(f"Few columns ({total_cols})")
    elif total_cols >= 20:
        fact_score += 1
        reasons.append(f"Many columns ({total_cols})")
    
    # Row count heuristic
    if row_count > 10000:
        fact_score += 2
        reasons.append(f"High row count ({row_count:,})")
    elif row_count > 0 and row_count <= 1000:
        dim_score += 1
        reasons.append(f"Low row count ({row_count:,})")
    
    # Determine role based on scores
    if fact_score > dim_score:
        confidence = min(0.9, 0.5 + (fact_score - dim_score) * 0.1)
        return ("fact", confidence, "; ".join(reasons) if reasons else "Column analysis suggests fact table")
    elif dim_score > fact_score:
        confidence = min(0.9, 0.5 + (dim_score - fact_score) * 0.1)
        return ("dimension", confidence, "; ".join(reasons) if reasons else "Column analysis suggests dimension table")
    else:
        # Default to fact if uncertain
        return ("fact", 0.5, "Uncertain - defaulting to fact table")


def get_table_row_counts(tables: List[str]) -> Dict[str, int]:
    """Get row counts for tables (sampling for performance)."""
    engine = get_engine()
    settings = get_settings()
    counts = {}
    
    with engine.connect() as conn:
        for table_name in tables[:50]:  # Limit to 50 tables for performance
            try:
                # Use COUNT for accurate count (could use EXPLAIN for estimates on large tables)
                if settings.db.dialect.lower() == "mysql":
                    # MySQL can use table stats for approximate count
                    result = conn.execute(text(f"""
                        SELECT TABLE_ROWS 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :table
                    """), {"db": settings.db.database, "table": table_name})
                    row = result.fetchone()
                    counts[table_name] = row[0] if row and row[0] else 0
                else:
                    # For other databases, use COUNT (limited sample)
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    counts[table_name] = result.scalar() or 0
            except Exception:
                counts[table_name] = 0
    
    return counts


def auto_analyze_and_map_tables(snapshot: SchemaSnapshot, include_row_counts: bool = True) -> Dict[str, Any]:
    """
    Automatically analyze all tables and create mappings.
    Returns analysis results with fact/dimension classifications.
    """
    results = {
        "analyzed_tables": [],
        "fact_tables": [],
        "dimension_tables": [],
        "mappings_created": 0,
    }
    
    # Get row counts if requested
    row_counts = {}
    if include_row_counts:
        try:
            row_counts = get_table_row_counts([t.name for t in snapshot.tables])
        except Exception:
            pass  # Continue without row counts
    
    # Analyze each table
    new_mappings = []
    for table in snapshot.tables:
        row_count = row_counts.get(table.name, 0)
        role, confidence, reason = analyze_table_type(table, row_count)
        
        analysis = {
            "table": table.name,
            "role": role,
            "confidence": confidence,
            "reason": reason,
            "row_count": row_count,
            "column_count": len(table.columns),
            "fk_count": sum(1 for c in table.columns if c.is_foreign),
        }
        results["analyzed_tables"].append(analysis)
        
        if role == "fact":
            results["fact_tables"].append(table.name)
        else:
            results["dimension_tables"].append(table.name)
        
        # Create mapping
        new_mappings.append(TableMapping(
            table=table.name,
            role=role,
            priority="silver",
            tenant_column="tenant_id" if any(c.name == "tenant_id" for c in table.columns) else "",
            business_name=f"Auto-detected {role} table"
        ))
    
    # Save mappings
    current_mappings = get_mapping_state()
    
    # Only add new mappings for tables not already mapped
    existing_tables = {m.table for m in current_mappings.tables}
    for mapping in new_mappings:
        if mapping.table not in existing_tables:
            current_mappings.tables.append(mapping)
            results["mappings_created"] += 1
    
    save_mapping_state(current_mappings)
    
    return results

