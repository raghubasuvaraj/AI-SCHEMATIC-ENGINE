"""
Join routes for managing table relationships and join graph.
"""
from fastapi import APIRouter, HTTPException
from backend.app.models.join import JoinEdge
from backend.app.services.join_service import (
    approve_join,
    get_join_graph,
    suggest_from_schema,
    remove_join,
    clear_all_joins,
    get_join_details,
)
from backend.app.services.schema_service import load_cached_schema, introspect_schema

router = APIRouter(prefix="/joins", tags=["joins"])


@router.get("", summary="List approved joins")
def list_joins():
    """Get all joins in the graph."""
    return get_join_graph()


@router.get("/details", summary="Get detailed join information with statistics")
def get_details():
    """
    Get comprehensive join details including:
    - Total join count
    - Approved join count
    - Tables with joins
    - Joins grouped by table
    """
    return get_join_details()


@router.get("/suggestions", summary="Suggest joins from foreign keys (requires schema)")
def suggest_joins():
    """Auto-suggest joins based on foreign key relationships in schema."""
    snapshot = load_cached_schema() or introspect_schema()
    suggestions = suggest_from_schema(snapshot)
    return {
        "suggestions": [s.model_dump() for s in suggestions],
        "count": len(suggestions),
    }


@router.post("/approve", summary="Approve a join edge")
def approve(edge: JoinEdge):
    """Add or update an approved join."""
    if not edge.left_table or not edge.right_table:
        raise HTTPException(status_code=400, detail="Invalid join payload - tables required")
    if not edge.left_column or not edge.right_column:
        raise HTTPException(status_code=400, detail="Invalid join payload - columns required")
    return approve_join(edge)


@router.delete("/remove", summary="Remove a specific join")
def remove(payload: dict):
    """
    Remove a specific join from the graph.
    
    Required fields:
    - left_table: Source table name
    - left_column: Source column name
    - right_table: Target table name
    - right_column: Target column name
    """
    left_table = payload.get("left_table")
    left_column = payload.get("left_column")
    right_table = payload.get("right_table")
    right_column = payload.get("right_column")
    
    if not all([left_table, left_column, right_table, right_column]):
        raise HTTPException(
            status_code=400, 
            detail="All fields required: left_table, left_column, right_table, right_column"
        )
    
    return remove_join(left_table, left_column, right_table, right_column)


@router.delete("/clear", summary="Clear all approved joins")
def clear():
    """
    Remove ALL approved joins from the graph.
    This action cannot be undone.
    """
    result = clear_all_joins()
    return {
        "message": "All joins cleared successfully",
        "joins": result.joins,
    }


@router.post("/bulk-approve", summary="Approve multiple joins at once")
def bulk_approve(payload: dict):
    """
    Approve multiple joins in a single request.
    
    Expected payload:
    {
        "joins": [
            {"left_table": "...", "left_column": "...", "right_table": "...", "right_column": "...", "join_type": "LEFT JOIN"}
        ]
    }
    """
    joins = payload.get("joins", [])
    if not joins:
        raise HTTPException(status_code=400, detail="No joins provided")
    
    approved = []
    errors = []
    
    for i, j in enumerate(joins):
        try:
            edge = JoinEdge(
                left_table=j.get("left_table"),
                left_column=j.get("left_column"),
                right_table=j.get("right_table"),
                right_column=j.get("right_column"),
                join_type=j.get("join_type", "LEFT JOIN"),
                approved=True,
            )
            approve_join(edge)
            approved.append(edge.model_dump())
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    
    return {
        "approved": len(approved),
        "errors": errors,
        "joins": approved,
    }
