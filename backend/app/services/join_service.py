from typing import List
from backend.app.models.join import JoinEdge, JoinGraph
from backend.app.models.schema import SchemaSnapshot
from backend.app.storage.state_store import JsonState

join_store = JsonState("backend/app/storage/approved_joins.json")


def get_join_graph() -> JoinGraph:
    data = join_store.load(default={"joins": []})
    return JoinGraph.model_validate(data)


def save_join_graph(graph: JoinGraph) -> None:
    join_store.save(graph.model_dump())


def suggest_from_schema(snapshot: SchemaSnapshot) -> List[JoinEdge]:
    suggestions: List[JoinEdge] = []
    for table in snapshot.tables:
        for col in table.columns:
            if col.is_foreign and col.foreign_key:
                fk = col.foreign_key
                suggestions.append(
                    JoinEdge(
                        left_table=table.name,
                        left_column=col.name,
                        right_table=fk.ref_table,
                        right_column=fk.ref_column,
                        constraint_name=fk.constraint_name,
                        approved=True,  # Auto-approve FK-based joins
                    )
                )
    return suggestions


def auto_approve_joins_from_schema(snapshot: SchemaSnapshot) -> JoinGraph:
    """
    Automatically approve all joins based on foreign key relationships in the schema.
    This removes the need for manual join approval.
    """
    graph = get_join_graph()
    existing_keys = {
        (j.left_table, j.left_column, j.right_table, j.right_column)
        for j in graph.joins
    }
    
    new_joins = []
    for table in snapshot.tables:
        for col in table.columns:
            if col.is_foreign and col.foreign_key:
                fk = col.foreign_key
                key = (table.name, col.name, fk.ref_table, fk.ref_column)
                
                if key not in existing_keys:
                    new_joins.append(
                        JoinEdge(
                            left_table=table.name,
                            left_column=col.name,
                            right_table=fk.ref_table,
                            right_column=fk.ref_column,
                            constraint_name=fk.constraint_name,
                            join_type="LEFT JOIN",
                            approved=True,
                        )
                    )
                    existing_keys.add(key)
    
    if new_joins:
        graph.joins.extend(new_joins)
        save_join_graph(graph)
    
    return graph


def approve_join(edge: JoinEdge) -> JoinGraph:
    graph = get_join_graph()
    key = (
        edge.left_table,
        edge.left_column,
        edge.right_table,
        edge.right_column,
    )
    existing = {
        (
            j.left_table,
            j.left_column,
            j.right_table,
            j.right_column,
        ): j
        for j in graph.joins
    }
    edge.approved = True
    existing[key] = edge
    graph.joins = list(existing.values())
    save_join_graph(graph)
    return graph


def remove_join(left_table: str, left_column: str, right_table: str, right_column: str) -> JoinGraph:
    """Remove a specific join from the graph."""
    graph = get_join_graph()
    key = (left_table, left_column, right_table, right_column)
    # Also check reverse key
    reverse_key = (right_table, right_column, left_table, left_column)
    
    graph.joins = [
        j for j in graph.joins
        if (j.left_table, j.left_column, j.right_table, j.right_column) not in [key, reverse_key]
    ]
    save_join_graph(graph)
    return graph


def clear_all_joins() -> JoinGraph:
    """Clear all approved joins."""
    graph = JoinGraph(joins=[])
    save_join_graph(graph)
    return graph


def get_join_details() -> dict:
    """Get detailed join information including statistics."""
    graph = get_join_graph()
    
    # Collect statistics
    tables_with_joins = set()
    for j in graph.joins:
        tables_with_joins.add(j.left_table)
        tables_with_joins.add(j.right_table)
    
    # Group by left table
    joins_by_table = {}
    for j in graph.joins:
        if j.left_table not in joins_by_table:
            joins_by_table[j.left_table] = []
        joins_by_table[j.left_table].append({
            "to_table": j.right_table,
            "left_column": j.left_column,
            "right_column": j.right_column,
            "join_type": j.join_type or "LEFT JOIN",
            "approved": j.approved,
        })
    
    return {
        "total_joins": len(graph.joins),
        "approved_joins": len([j for j in graph.joins if j.approved]),
        "tables_with_joins": len(tables_with_joins),
        "joins_by_table": joins_by_table,
        "joins": [j.model_dump() for j in graph.joins],
    }
