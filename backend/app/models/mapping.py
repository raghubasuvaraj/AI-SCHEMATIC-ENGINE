from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TableMapping(BaseModel):
    table: str
    role: str = Field(..., description="fact|dimension")
    priority: str = Field("silver", description="gold|silver|bronze")
    business_name: Optional[str] = None
    tenant_column: Optional[str] = None


class ColumnMapping(BaseModel):
    table: str
    column: str
    business_meaning: Optional[str] = None
    enum_values: Optional[List[str]] = None


class MappingState(BaseModel):
    tables: List[TableMapping] = []
    columns: List[ColumnMapping] = []

    def as_lookup(self) -> Dict[str, TableMapping]:
        return {t.table: t for t in self.tables}
