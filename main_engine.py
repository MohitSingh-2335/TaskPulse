from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Config
from src.core.calendar_sync import get_calendar_service
from src.core.task_service import TaskService


def schedule_tasks():
    print("[TaskPulse] Starting Dynamic Task Engine...")
    calendar_service = get_calendar_service()
    if not calendar_service:
        print("[INFO] Google Calendar credentials not detected. Scheduling locally in database.")

    service = TaskService()
    result = service.schedule_pending_tasks(
        calendar_service=calendar_service,
        start_hour=Config.SCHEDULE_START_HOUR,
        buffer_minutes=Config.SCHEDULE_BUFFER_MINUTES,
        timezone_name=Config.DEFAULT_TIME_ZONE,
    )

    print(f"[OK] Successfully scheduled {result.get('count', 0)} tasks for {result.get('date')}!")
    for item in result.get("scheduled", []):
        task = item.get("task", {})
        print(f"  * [{item.get('start_at')}] {task.get('content')} ({task.get('remaining_minutes')}m)")


if __name__ == "__main__":
    schedule_tasks()