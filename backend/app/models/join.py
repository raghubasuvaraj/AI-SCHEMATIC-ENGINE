from typing import List
from pydantic import BaseModel


class JoinEdge(BaseModel):
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    constraint_name: str | None = None
    join_type: str | None = "LEFT JOIN"
    approved: bool = False


class JoinGraph(BaseModel):
    joins: List[JoinEdge] = []
