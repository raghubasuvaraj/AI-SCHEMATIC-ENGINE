from typing import List, Optional, Literal
from pydantic import BaseModel, Field


Aggregation = Literal["count", "sum", "avg", "min", "max"]
Comparator = Literal["=", "!=", ">", "<", ">=", "<=", "in", "between", "like"]


class Metric(BaseModel):
    column: str
    aggregation: Aggregation = "sum"
    alias: Optional[str] = None


class Filter(BaseModel):
    column: str
    operator: Comparator
    value: object


class CanonicalPlan(BaseModel):
    intent: str = Field("", description="LLM predicted intent label")
    fact_table: str = Field(..., description="Approved fact table name")
    dimensions: List[str] = []
    metrics: List[Metric] = []
    filters: List[Filter] = []
    group_by: List[str] = []
    order_by: List[str] = []
    limit: int = 100
