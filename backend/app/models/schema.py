from typing import List, Optional
from pydantic import BaseModel


class EnumValue(BaseModel):
    table: str
    column: str
    values: List[str]


class ForeignKey(BaseModel):
    column: str
    ref_table: str
    ref_column: str
    constraint_name: Optional[str] = None


class Column(BaseModel):
    name: str
    data_type: str
    is_nullable: bool
    is_primary: bool = False
    is_foreign: bool = False
    foreign_key: Optional[ForeignKey] = None
    default: Optional[str] = None
    comment: Optional[str] = None


class Table(BaseModel):
    name: str
    columns: List[Column]
    comment: Optional[str] = None


class SchemaSnapshot(BaseModel):
    tables: List[Table]
    enums: List[EnumValue] = []
    dialect: Optional[str] = None
    database: Optional[str] = None
