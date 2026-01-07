import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional


class JsonState:
    """
    Minimal JSON-backed storage with process-level locking.
    Intended for approvals, mappings, and audit configuration.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def load(self, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        with self._lock:
            if not self.path.exists():
                return default or {}
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)

    def save(self, data: Dict[str, Any]) -> None:
        with self._lock:
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
