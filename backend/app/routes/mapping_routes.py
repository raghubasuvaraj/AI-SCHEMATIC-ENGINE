from fastapi import APIRouter
from backend.app.models.mapping import ColumnMapping, TableMapping
from backend.app.services.mapping_service import (
    clear_mappings,
    get_mapping_state,
    upsert_column_mapping,
    upsert_table_mapping,
)

router = APIRouter(prefix="/mappings", tags=["mappings"])


@router.get("", summary="Get current human-approved mappings")
def get_mappings():
    return get_mapping_state()


@router.post("/table", summary="Approve or update table role/priority")
def save_table_mapping(payload: TableMapping):
    return upsert_table_mapping(payload)


@router.post("/column", summary="Capture business meaning or enums for a column")
def save_column_mapping(payload: ColumnMapping):
    return upsert_column_mapping(payload)


@router.delete("", summary="Clear all mappings")
def reset_mappings():
    clear_mappings()
    return {"status": "cleared"}
