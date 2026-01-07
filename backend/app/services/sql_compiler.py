from typing import Dict, List, Tuple
from backend.app.config import get_settings
from backend.app.models.plan import CanonicalPlan
from backend.app.models.join import JoinGraph, JoinEdge
from backend.app.models.schema import SchemaSnapshot


def _quote(identifier: str, dialect: str) -> str:
    if dialect == "postgres":
        return f'"{identifier}"'
    if dialect in ("mssql", "sqlserver"):
        return f"[{identifier}]"
    return f"`{identifier}`"


def _find_join(fact: str, dim: str, joins: JoinGraph) -> JoinEdge | None:
    for edge in joins.joins:
        if not edge.approved:
            continue
        if (edge.left_table == fact and edge.right_table == dim) or (
            edge.left_table == dim and edge.right_table == fact
        ):
            return edge
    return None


def _resolve_column_owner(column: str, plan: CanonicalPlan, snapshot: SchemaSnapshot) -> str:
    for table in [plan.fact_table, *plan.dimensions]:
        t = next((t for t in snapshot.tables if t.name == table), None)
        if t and any(c.name == column for c in t.columns):
            return table
    raise ValueError(f"Column {column} not found in plan tables")


def compile_sql(plan: CanonicalPlan, snapshot: SchemaSnapshot, joins: JoinGraph) -> Tuple[str, List[Tuple[str, object]]]:
    """
    Deterministically compiles a validated plan to SQL. Returns SQL string and parameters.
    """
    settings = get_settings()
    dialect = settings.db.dialect

    aliases: Dict[str, str] = {plan.fact_table: "f"}
    for idx, dim in enumerate(plan.dimensions, start=1):
        aliases[dim] = f"d{idx}"

    select_parts: List[str] = []
    group_parts: List[str] = []

    for col in plan.group_by:
        owner = _resolve_column_owner(col, plan, snapshot)
        select_parts.append(f"{aliases[owner]}.{_quote(col, dialect)} AS {col}")
        group_parts.append(f"{aliases[owner]}.{_quote(col, dialect)}")

    for metric in plan.metrics:
        owner = _resolve_column_owner(metric.column, plan, snapshot)
        agg_func = metric.aggregation.upper()
        alias = metric.alias or f"{metric.aggregation}_{metric.column}"
        select_parts.append(f"{agg_func}({aliases[owner]}.{_quote(metric.column, dialect)}) AS {_quote(alias, dialect)}")

    if not select_parts:
        select_parts.append("COUNT(*) AS row_count")

    from_clause = f"{_quote(plan.fact_table, dialect)} {aliases[plan.fact_table]}"
    join_clauses: List[str] = []
    for dim in plan.dimensions:
        join = _find_join(plan.fact_table, dim, joins)
        if not join:
            raise ValueError(f"No approved join for {dim}")
        left_alias = aliases[join.left_table]
        right_alias = aliases[join.right_table]
        join_clauses.append(
            f"LEFT JOIN {_quote(join.right_table, dialect)} {right_alias} "
            f"ON {left_alias}.{_quote(join.left_column, dialect)} = {right_alias}.{_quote(join.right_column, dialect)}"
            if join.left_table == plan.fact_table
            else f"LEFT JOIN {_quote(join.left_table, dialect)} {left_alias} "
            f"ON {right_alias}.{_quote(join.right_column, dialect)} = {left_alias}.{_quote(join.left_column, dialect)}"
        )

    where_parts: List[str] = []
    params: List[Tuple[str, object]] = []
    for idx, filt in enumerate(plan.filters):
        owner = _resolve_column_owner(filt.column, plan, snapshot)
        placeholder = f":p{idx}"
        where_parts.append(f"{aliases[owner]}.{_quote(filt.column, dialect)} {filt.operator} {placeholder}")
        params.append((placeholder, filt.value))

    sql = "SELECT " + ", ".join(select_parts)
    sql += " FROM " + from_clause
    if join_clauses:
        sql += " " + " ".join(join_clauses)
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)
    if group_parts:
        sql += " GROUP BY " + ", ".join(group_parts)
    if plan.order_by:
        order_parts = []
        # Collect metric aliases for order_by resolution
        metric_aliases = {m.alias or f"{m.aggregation}_{m.column}": m for m in plan.metrics}
        
        for col in plan.order_by:
            # Parse direction suffix (ASC/DESC)
            col_upper = col.upper()
            direction = ""
            col_name = col
            
            if col_upper.endswith(" DESC"):
                direction = " DESC"
                col_name = col[:-5].strip()
            elif col_upper.endswith(" ASC"):
                direction = " ASC"
                col_name = col[:-4].strip()
            
            # Check if it's a metric alias
            if col_name in metric_aliases:
                order_parts.append(f"{_quote(col_name, dialect)}{direction}")
            else:
                # Try to resolve as a table column
                try:
                    owner = _resolve_column_owner(col_name, plan, snapshot)
                    order_parts.append(f"{aliases[owner]}.{_quote(col_name, dialect)}{direction}")
                except ValueError:
                    # Skip invalid order_by columns instead of failing
                    continue
        
        if order_parts:
            sql += " ORDER BY " + ", ".join(order_parts)
    sql += f" LIMIT {min(plan.limit, settings.security.max_limit)}"
    return sql, params
