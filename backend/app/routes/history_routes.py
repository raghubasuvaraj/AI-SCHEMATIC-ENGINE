"""
API routes for query history management.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response
from typing import Dict, Any
from backend.app.services.history_service import (
    get_history, clear_history, 
    export_history_to_json, export_history_to_csv, export_history_to_text,
    export_history_to_excel, get_history_table
)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", summary="Get query history")
def list_history():
    """Get all stored query history."""
    history = get_history()
    return {
        "total": len(history.items),
        "items": [item.model_dump() for item in history.items]
    }


@router.get("/table", summary="Get query history as table format")
def get_table_view():
    """
    Get all query history formatted as a table for UI display.
    Returns: question, intent, query_plan, sql, status for each query.
    """
    table = get_history_table()
    return {
        "total": len(table),
        "columns": ["#", "Timestamp", "Question", "Intent", "Query Plan", "SQL", "Status", "Time (ms)", "Rows"],
        "rows": table
    }


@router.delete("/clear", summary="Clear query history")
def clear_all_history():
    """Clear all query history."""
    clear_history()
    return {"message": "History cleared", "total": 0}


@router.get("/export/json", summary="Export history as JSON")
def export_json():
    """Export all history as JSON."""
    return {"content": export_history_to_json(), "format": "json"}


@router.get("/export/csv", summary="Export history as CSV", response_class=PlainTextResponse)
def export_csv():
    """
    Export all history as CSV.
    Columns: id, timestamp, database, question, intent, query_plan, sql, status, execution_time_ms, row_count
    """
    csv_content = export_history_to_csv()
    return PlainTextResponse(
        content=csv_content, 
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=query_history.csv"}
    )


@router.get("/export/excel", summary="Export history as Excel")
def export_excel():
    """
    Export all history as Excel (.xlsx) file.
    Includes formatting, colored status cells, and frozen header.
    """
    excel_bytes = export_history_to_excel()
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=query_history.xlsx"}
    )


@router.get("/export/text", summary="Export history as text", response_class=PlainTextResponse)
def export_text():
    """Export all history as formatted text."""
    return PlainTextResponse(content=export_history_to_text(), media_type="text/plain")

