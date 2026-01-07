from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AuditRecord(BaseModel):
    timestamp: datetime
    user: Optional[str]
    request_id: str
    intent: Optional[str]
    plan: Dict[str, Any]
    sql: Optional[str] = None
    status: str
    message: Optional[str] = None
