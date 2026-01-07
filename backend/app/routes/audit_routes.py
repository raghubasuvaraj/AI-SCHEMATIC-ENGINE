from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.app.config import get_settings

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", summary="Return recent audit records")
def get_logs(limit: int = 50):
    settings = get_settings()
    path = Path(settings.audit_log_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="No audit logs yet")
    lines = path.read_text(encoding="utf-8").splitlines()
    return {"entries": lines[-limit:]}
