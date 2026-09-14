from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from src.core.database import get_database


class TelemetryTracker:
    """Tracks latency, token efficiency, and operational health."""

    def __init__(self, operation: str, model: Optional[str] = None):
        self.operation = operation
        self.model = model
        self.start_time: float = 0.0
        self.latency_ms: float = 0.0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.status: str = "success"
        self.error_message: Optional[str] = None

    def __enter__(self) -> TelemetryTracker:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.latency_ms = round((time.perf_counter() - self.start_time) * 1000, 2)
        if exc_type is not None:
            self.status = "error"
            self.error_message = str(exc_val)

        # Record to database
        try:
            db = get_database()
            db.log_telemetry(
                operation=self.operation,
                model=self.model or "unknown",
                latency_ms=self.latency_ms,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                status=self.status,
                error_message=self.error_message,
            )
        except Exception:
            pass  # Avoid telemetry recording failure interfering with main operation

    def set_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    def set_model(self, model_name: str) -> None:
        self.model = model_name


def get_telemetry_summary() -> Dict[str, Any]:
    """Computes high-level observability metrics from recent logs."""
    try:
        db = get_database()
        logs = db.list_telemetry(limit=100)
    except Exception:
        return {"total_calls": 0, "avg_latency_ms": 0, "success_rate": 100, "recent_logs": []}

    if not logs:
        return {"total_calls": 0, "avg_latency_ms": 0, "success_rate": 100, "recent_logs": []}

    total = len(logs)
    successes = sum(1 for log in logs if log.get("status") == "success")
    avg_latency = round(sum(float(log.get("latency_ms", 0)) for log in logs) / total, 1)
    success_rate = round((successes / total) * 100, 1)

    return {
        "total_calls": total,
        "avg_latency_ms": avg_latency,
        "success_rate": success_rate,
        "recent_logs": logs[:15],
    }
