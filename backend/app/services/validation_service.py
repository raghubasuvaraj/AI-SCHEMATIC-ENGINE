"""
Comprehensive validation service for query plans.
Validates against schema, mappings, joins, and security rules.
"""
from typing import List, Tuple, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.config import get_settings
from backend.app.models.join import JoinGraph
from backend.app.models.mapping import MappingState
from backend.app.models.plan import CanonicalPlan, Aggregation
from backend.app.models.schema import SchemaSnapshot


class ValidationError(BaseModel):
    """Single validation error with details."""
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Complete validation result."""
    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    validated_plan: Optional[Dict[str, Any]] = None


class PlanValidationError(Exception):
    """Exception raised when plan validation fails."""
    def __init__(self, errors: List[str], validation_result: Optional[ValidationResult] = None):
        self.errors = errors
        self.validation_result = validation_result
        super().__init__("; ".join(errors))


def _table_lookup(snapshot: SchemaSnapshot) -> Tuple[Dict, Dict]:
    """Build lookup maps for tables and columns."""
    table_map = {t.name: t for t in snapshot.tables}
    column_map = {
        (t.name, c.name): c
        for t in snapshot.tables
        for c in t.columns
    }
    return table_map, column_map


def _has_approved_join(fact: str, dim: str, joins: JoinGraph) -> bool:
    """Check if there's an approved join between fact and dimension."""
    for edge in joins.joins:
        if not edge.approved:
            continue
        if (edge.left_table == fact and edge.right_table == dim) or (
            edge.left_table == dim and edge.right_table == fact
        ):
            return True
    return False


def _get_column_suggestions(column: str, table_map: Dict, allowed_tables: set) -> List[str]:
    """Get suggestions for similar column names."""
    suggestions = []
    column_lower = column.lower()
    
    for table_name in allowed_tables:
        if table_name in table_map:
            for col in table_map[table_name].columns:
                if column_lower in col.name.lower() or col.name.lower() in column_lower:
                    suggestions.append(f"{table_name}.{col.name}")
    
    return suggestions[:3]  # Return top 3 suggestions


def validate_question(question: str) -> ValidationResult:
    """Validate the input question."""
    errors = []
    warnings = []
    
    if not question or not question.strip():
        errors.append(ValidationError(
            code="EMPTY_QUESTION",
            message="Question cannot be empty",
            field="question",
            suggestion="Please provide a natural language query"
        ))
    elif len(question.strip()) < 5:
        errors.append(ValidationError(
            code="QUESTION_TOO_SHORT",
            message="Question is too short to be meaningful",
            field="question",
            suggestion="Please provide a more detailed question"
        ))
    elif len(question) > 2000:
        errors.append(ValidationError(
            code="QUESTION_TOO_LONG",
            message="Question exceeds maximum length of 2000 characters",
            field="question",
            suggestion="Please shorten your question"
        ))
    
    # Check for potentially dangerous patterns
    dangerous_keywords = ["drop", "delete", "truncate", "alter", "create", "insert", "update"]
    question_lower = question.lower()
    for keyword in dangerous_keywords:
        if keyword in question_lower:
            warnings.append(ValidationError(
                code="SUSPICIOUS_KEYWORD",
                message=f"Question contains potentially dangerous keyword: '{keyword}'",
                field="question",
                suggestion="This keyword will be blocked during SQL generation"
            ))
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_plan(
    plan: CanonicalPlan,
    snapshot: SchemaSnapshot,
    mappings: MappingState,
    joins: JoinGraph,
) -> ValidationResult:
    """
    Comprehensive validation of a query plan against schema, mappings, and joins.
    Returns detailed validation result with errors and warnings.
    """
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    table_map, column_map = _table_lookup(snapshot)
    settings = get_settings()

    approved_facts = {t.table for t in mappings.tables if t.role == "fact"}
    approved_dims = {t.table for t in mappings.tables if t.role == "dimension"}
    all_tables = set(table_map.keys())

    # ===== Validate Fact Table =====
    if not plan.fact_table:
        errors.append(ValidationError(
            code="MISSING_FACT_TABLE",
            message="No fact table specified in the plan",
            field="fact_table",
            suggestion=f"Available fact tables: {list(approved_facts)}" if approved_facts else "Please map some tables as fact tables first"
        ))
    elif plan.fact_table not in approved_facts:
        if plan.fact_table in all_tables:
            errors.append(ValidationError(
                code="FACT_NOT_APPROVED",
                message=f"Table '{plan.fact_table}' exists but is not approved as a fact table",
                field="fact_table",
                suggestion=f"Approved fact tables: {list(approved_facts)}"
            ))
        else:
            errors.append(ValidationError(
                code="FACT_NOT_FOUND",
                message=f"Fact table '{plan.fact_table}' not found in schema",
                field="fact_table",
                suggestion=f"Available tables: {list(all_tables)[:10]}..."
            ))
    elif plan.fact_table not in table_map:
        errors.append(ValidationError(
            code="FACT_SCHEMA_MISMATCH",
            message=f"Fact table '{plan.fact_table}' not found in current schema snapshot",
            field="fact_table",
            suggestion="Try re-introspecting the schema"
        ))

    # ===== Validate Dimensions =====
    for dim in plan.dimensions:
        if dim not in approved_dims:
            if dim in all_tables:
                errors.append(ValidationError(
                    code="DIM_NOT_APPROVED",
                    message=f"Table '{dim}' exists but is not approved as a dimension",
                    field="dimensions",
                    suggestion=f"Approved dimensions: {list(approved_dims)}"
                ))
            else:
                errors.append(ValidationError(
                    code="DIM_NOT_FOUND",
                    message=f"Dimension '{dim}' not found in schema",
                    field="dimensions"
                ))
        
        if dim not in table_map:
            errors.append(ValidationError(
                code="DIM_SCHEMA_MISMATCH",
                message=f"Dimension '{dim}' not in current schema snapshot",
                field="dimensions"
            ))
        
        if plan.fact_table and not _has_approved_join(plan.fact_table, dim, joins):
            errors.append(ValidationError(
                code="NO_APPROVED_JOIN",
                message=f"No approved join between fact '{plan.fact_table}' and dimension '{dim}'",
                field="dimensions",
                suggestion="Please approve a join relationship between these tables"
            ))

    # ===== Validate Metrics =====
    allowed_aggs: List[Aggregation] = ["count", "sum", "avg", "min", "max"]
    allowed_tables = {plan.fact_table, *plan.dimensions}
    
    for i, metric in enumerate(plan.metrics):
        if metric.aggregation not in allowed_aggs:
            errors.append(ValidationError(
                code="INVALID_AGGREGATION",
                message=f"Aggregation '{metric.aggregation}' is not allowed",
                field=f"metrics[{i}].aggregation",
                suggestion=f"Allowed aggregations: {allowed_aggs}"
            ))
        
        # Check if column exists in fact or dimensions
        column_found = False
        if plan.fact_table and (plan.fact_table, metric.column) in column_map:
            column_found = True
        for dim in plan.dimensions:
            if (dim, metric.column) in column_map:
                column_found = True
                break
        
        if not column_found:
            suggestions = _get_column_suggestions(metric.column, table_map, allowed_tables)
            errors.append(ValidationError(
                code="METRIC_COLUMN_NOT_FOUND",
                message=f"Metric column '{metric.column}' not found in fact table or dimensions",
                field=f"metrics[{i}].column",
                suggestion=f"Similar columns: {suggestions}" if suggestions else None
            ))
        else:
            # Validate aggregation makes sense for the data type
            col = None
            for t in allowed_tables:
                if (t, metric.column) in column_map:
                    col = column_map[(t, metric.column)]
                    break
            
            if col and metric.aggregation in ("sum", "avg"):
                numeric_types = {"int", "integer", "bigint", "smallint", "tinyint", 
                               "decimal", "numeric", "float", "double", "real", "money"}
                if not any(nt in col.data_type.lower() for nt in numeric_types):
                    warnings.append(ValidationError(
                        code="NON_NUMERIC_AGGREGATION",
                        message=f"Column '{metric.column}' has type '{col.data_type}', {metric.aggregation} may not work as expected",
                        field=f"metrics[{i}]"
                    ))

    # ===== Validate Filters =====
    for i, filt in enumerate(plan.filters):
        column_found = any((t, filt.column) in column_map for t in allowed_tables)
        if not column_found:
            suggestions = _get_column_suggestions(filt.column, table_map, allowed_tables)
            errors.append(ValidationError(
                code="FILTER_COLUMN_NOT_FOUND",
                message=f"Filter column '{filt.column}' not found in allowed tables",
                field=f"filters[{i}].column",
                suggestion=f"Similar columns: {suggestions}" if suggestions else None
            ))
        
        # Validate operator
        valid_operators = ["=", "!=", ">", "<", ">=", "<=", "in", "between", "like"]
        if filt.operator not in valid_operators:
            errors.append(ValidationError(
                code="INVALID_OPERATOR",
                message=f"Filter operator '{filt.operator}' is not valid",
                field=f"filters[{i}].operator",
                suggestion=f"Valid operators: {valid_operators}"
            ))

    # ===== Validate Group By / Order By =====
    for i, col in enumerate(plan.group_by):
        if not any((t, col) in column_map for t in allowed_tables):
            errors.append(ValidationError(
                code="GROUPBY_COLUMN_NOT_FOUND",
                message=f"Group by column '{col}' not found",
                field=f"group_by[{i}]"
            ))

    # Collect metric aliases for order_by validation
    metric_aliases = {m.alias for m in plan.metrics if m.alias}
    metric_columns = {m.column for m in plan.metrics}
    
    for i, col in enumerate(plan.order_by):
        # Strip ASC/DESC direction suffix if present
        col_name = col.upper().replace(" DESC", "").replace(" ASC", "").strip().lower()
        # Also handle case where column name is the original case
        col_clean = col.split()[0] if " " in col else col
        
        # Check if column is a valid metric alias, metric column, or table column
        is_valid = (
            col_clean in metric_aliases or
            col_clean in metric_columns or
            col_name in metric_aliases or
            col_name in metric_columns or
            any((t, col_clean) in column_map for t in allowed_tables) or
            any((t, col_name) in column_map for t in allowed_tables)
        )
        
        if not is_valid:
            # Downgrade to warning instead of error - order_by is not critical
            warnings.append(ValidationError(
                code="ORDERBY_COLUMN_NOT_FOUND",
                message=f"Order by column '{col}' not found - will be ignored",
                field=f"order_by[{i}]"
            ))

    # ===== Validate Tenant Filter (Security) =====
    tenant_column = settings.security.tenant_column
    tenant_filter_found = any(f.column == tenant_column for f in plan.filters)
    
    if not tenant_filter_found:
        # Check if tenant column exists in allowed tables
        tenant_exists = any((t, tenant_column) in column_map for t in allowed_tables)
        if tenant_exists and settings.security.require_tenant_filter:
            # Only error if tenant filter is required by config
            errors.append(ValidationError(
                code="MISSING_TENANT_FILTER",
                message=f"Required tenant filter on '{tenant_column}' is missing",
                field="filters",
                suggestion=f"Add a filter with column='{tenant_column}' for security"
            ))
        elif tenant_exists:
            # Just a warning if tenant column exists but filter not required
            warnings.append(ValidationError(
                code="TENANT_FILTER_RECOMMENDED",
                message=f"Tenant column '{tenant_column}' exists but no filter applied",
                field="filters",
                suggestion=f"Consider adding a filter on '{tenant_column}' for better data isolation"
            ))

    # ===== Validate Limit =====
    if plan.limit > settings.security.max_limit:
        errors.append(ValidationError(
            code="LIMIT_EXCEEDED",
            message=f"Limit {plan.limit} exceeds maximum allowed {settings.security.max_limit}",
            field="limit",
            suggestion=f"Use a limit of {settings.security.max_limit} or less"
        ))
    elif plan.limit <= 0:
        errors.append(ValidationError(
            code="INVALID_LIMIT",
            message="Limit must be a positive integer",
            field="limit"
        ))

    # Build result
    result = ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        validated_plan=plan.model_dump() if len(errors) == 0 else None
    )

    if not result.is_valid:
        raise PlanValidationError(
            [f"[{e.code}] {e.message}" for e in errors],
            validation_result=result
        )
    
    return result


def validate_sql_safety(sql: str) -> ValidationResult:
    """Validate SQL for safety (no DDL/DML, no multiple statements)."""
    errors = []
    warnings = []
    
    lowered = sql.strip().lower()
    
    # Must be a SELECT statement
    if not lowered.startswith("select"):
        errors.append(ValidationError(
            code="NOT_SELECT",
            message="Only SELECT statements are allowed",
            suggestion="The query must start with SELECT"
        ))
    
    # Check for forbidden keywords
    forbidden = {
        "insert": "INSERT statements are blocked",
        "update": "UPDATE statements are blocked", 
        "delete": "DELETE statements are blocked",
        "drop": "DROP statements are blocked",
        "alter": "ALTER statements are blocked",
        "truncate": "TRUNCATE statements are blocked",
        "create": "CREATE statements are blocked",
        "grant": "GRANT statements are blocked",
        "revoke": "REVOKE statements are blocked",
        "exec": "EXEC/EXECUTE statements are blocked",
        "execute": "EXECUTE statements are blocked",
    }
    
    for keyword, message in forbidden.items():
        # Check for keyword as a word (not part of another word)
        if f" {keyword} " in f" {lowered} " or lowered.startswith(f"{keyword} "):
            errors.append(ValidationError(
                code="FORBIDDEN_KEYWORD",
                message=message
            ))
    
    # Check for multiple statements
    if ";" in lowered[:-1]:  # Ignore trailing semicolon
        errors.append(ValidationError(
            code="MULTIPLE_STATEMENTS",
            message="Multiple SQL statements are blocked",
            suggestion="Submit one query at a time"
        ))
    
    # Check for system catalog access
    system_catalogs = ["information_schema", "pg_catalog", "sys.", "sysobjects", "master."]
    for catalog in system_catalogs:
        if catalog in lowered:
            errors.append(ValidationError(
                code="SYSTEM_CATALOG_ACCESS",
                message=f"Access to system catalog '{catalog}' is blocked in compiled SQL"
            ))
    
    # Check for comments (potential SQL injection)
    if "--" in sql or "/*" in sql:
        warnings.append(ValidationError(
            code="SQL_COMMENTS",
            message="SQL contains comments which could indicate injection attempt"
        ))
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
