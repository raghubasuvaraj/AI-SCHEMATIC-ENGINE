from typing import Optional
from backend.app.models.mapping import ColumnMapping, MappingState, TableMapping
from backend.app.storage.state_store import JsonState

mapping_store = JsonState("backend/app/storage/mappings.json")


def get_mapping_state() -> MappingState:
    data = mapping_store.load(default={"tables": [], "columns": []})
    return MappingState.model_validate(data)


def save_mapping_state(state: MappingState) -> None:
    mapping_store.save(state.model_dump())


def upsert_table_mapping(payload: TableMapping) -> MappingState:
    state = get_mapping_state()
    existing = {t.table: t for t in state.tables}
    existing[payload.table] = payload
    state.tables = list(existing.values())
    save_mapping_state(state)
    return state


def upsert_column_mapping(payload: ColumnMapping) -> MappingState:
    state = get_mapping_state()
    key = (payload.table, payload.column)
    existing = {(c.table, c.column): c for c in state.columns}
    existing[key] = payload
    state.columns = list(existing.values())
    save_mapping_state(state)
    return state


def clear_mappings() -> None:
    save_mapping_state(MappingState())
