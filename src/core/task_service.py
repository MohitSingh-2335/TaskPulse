from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.config import Config
from src.core.calendar_sync import format_calendar_event, get_or_create_target_calendar
from src.core.database import SQLiteAdapter, get_database

PRIORITY_MAP = {"High": 1, "Medium": 2, "Low": 3}
PRIORITY_LABELS = {1: "High", 2: "Medium", 3: "Low"}


def normalize_priority(value: Any) -> Dict[str, Any]:
    """Normalizes any priority input into rank (1-3) and label (High, Medium, Low)."""
    if isinstance(value, int):
        rank = min(3, max(1, value))
        return {"rank": rank, "label": PRIORITY_LABELS[rank]}

    text = str(value or "").strip().title()
    rank = PRIORITY_MAP.get(text, 2)
    return {"rank": rank, "label": PRIORITY_LABELS[rank]}


def parse_time_zone(value: Optional[str] = None):
    zone_name = value or Config.DEFAULT_TIME_ZONE
    try:
        return ZoneInfo(zone_name), zone_name
    except ZoneInfoNotFoundError:
        return timezone.utc, "UTC"


class TaskService:
    """Core domain service managing the full lifecycle of tasks, scheduling, and review."""

    def __init__(self, db: Optional[SQLiteAdapter] = None):
        self.db = db or get_database()

    def create_goal_plan(self, payload: Dict[str, Any], source: str = "api") -> Dict[str, Any]:
        """Creates a Goal, its Tasks, and associated Subtasks."""
        goal_data = payload.get("goal") or {}
        title = goal_data.get("title") or "Dynamic Task Goal"
        timeframe = goal_data.get("timeframe") or "Daily"

        goal = self.db.insert_goal(title=title, timeframe=timeframe, source=source)
        goal_id = goal["id"]

        tasks_payload = payload.get("tasks") or []
        created_tasks: List[Dict[str, Any]] = []

        for order, t in enumerate(tasks_payload, start=1):
            pri = normalize_priority(t.get("priority"))
            est = int(t.get("estimated_minutes") or t.get("duration_minutes") or 30)
            rem = int(t.get("remaining_minutes") or est)

            parent_task = self.db.insert_task({
                "goal_id": goal_id,
                "parent_task_id": None,
                "task_kind": "task",
                "content": t.get("content") or t.get("title") or "Untitled Task",
                "level": 1,
                "estimated_minutes": est,
                "remaining_minutes": rem,
                "execution_order": int(t.get("execution_order") or order),
                "priority": pri["label"],
                "priority_rank": pri["rank"],
                "status": t.get("status") or "Pending",
                "source": source,
            })
            created_tasks.append(parent_task)

            # Subtasks
            for sub_order, sub in enumerate(t.get("sub_tasks") or [], start=1):
                sub_pri = normalize_priority(sub.get("priority") or pri["label"])
                sub_est = int(sub.get("estimated_minutes") or 15)
                child_task = self.db.insert_task({
                    "goal_id": goal_id,
                    "parent_task_id": parent_task["id"],
                    "task_kind": "subtask",
                    "content": sub.get("content") or sub.get("title") or "Untitled Sub-task",
                    "level": 2,
                    "estimated_minutes": sub_est,
                    "remaining_minutes": sub_est,
                    "execution_order": int(sub.get("execution_order") or sub_order),
                    "priority": sub_pri["label"],
                    "priority_rank": sub_pri["rank"],
                    "status": "Pending",
                    "source": source,
                })
                created_tasks.append(child_task)

        return {
            "goal": goal,
            "tasks": created_tasks,
            "counts": {
                "tasks": len([x for x in created_tasks if x.get("task_kind") == "task"]),
                "sub_tasks": len([x for x in created_tasks if x.get("task_kind") == "subtask"]),
            },
        }

    def list_pending_parent_tasks(self) -> List[Dict[str, Any]]:
        """Returns pending parent tasks ordered by priority and execution order."""
        return self.db.list_tasks(status="Pending", parent_task_id=None)

    def list_scheduled_parent_tasks(self) -> List[Dict[str, Any]]:
        """Returns scheduled parent tasks."""
        return self.db.list_tasks(status="Scheduled", parent_task_id=None)

    def get_task_children(self, task_id: int) -> List[Dict[str, Any]]:
        """Returns all subtasks belonging to a parent task."""
        return self.db.list_tasks(parent_task_id=task_id)

    def render_subtasks_checklist(self, task_id: int) -> str:
        children = self.get_task_children(task_id)
        return "\n".join(f"- [ ] {c.get('content')}" for c in children)

    def schedule_pending_tasks(
        self,
        calendar_service: Optional[Any] = None,
        start_hour: int = 7,
        buffer_minutes: int = 15,
        timezone_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Time-blocks pending tasks for tomorrow, syncing to Google Calendar if available."""
        zone, display_zone = parse_time_zone(timezone_name)
        tomorrow = datetime.now(zone) + timedelta(days=1)
        current_slot = tomorrow.replace(hour=start_hour, minute=0, second=0, microsecond=0)

        pending = self.list_pending_parent_tasks()
        scheduled_results: List[Dict[str, Any]] = []
        failed_results: List[Dict[str, Any]] = []

        target_cal_id = None
        if calendar_service:
            try:
                target_cal_id = get_or_create_target_calendar(calendar_service)
            except Exception as exc:
                failed_results.append({"task_id": "calendar_init", "error": f"Could not access sub-calendar: {exc}"})

        for task in pending:
            duration = int(task.get("remaining_minutes") or task.get("estimated_minutes") or 30)
            start_at = current_slot
            end_at = start_at + timedelta(minutes=duration)

            event_id = None
            checklist = self.render_subtasks_checklist(task["id"])

            if calendar_service and target_cal_id:
                event_body = format_calendar_event(task, checklist, start_at, end_at, display_zone)
                try:
                    res = calendar_service.events().insert(calendarId=target_cal_id, body=event_body).execute()
                    event_id = res.get("id")
                except Exception as exc:
                    failed_results.append({"task_id": task["id"], "error": str(exc)})

            # Update task record in DB
            updated_task = self.db.update_task(task["id"], {
                "status": "Scheduled",
                "scheduled_start_at": start_at.isoformat(),
                "scheduled_end_at": end_at.isoformat(),
                "calendar_event_id": event_id,
            })

            scheduled_results.append({
                "task": updated_task,
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
                "calendar_event_id": event_id,
            })

            current_slot = end_at + timedelta(minutes=buffer_minutes)

        return {
            "timezone": display_zone,
            "start_hour": start_hour,
            "date": tomorrow.strftime("%Y-%m-%d"),
            "scheduled": scheduled_results,
            "failed": failed_results,
            "count": len(scheduled_results),
        }

    def review_snapshot(self) -> Dict[str, Any]:
        """Provides evening review summary grouped by task statuses."""
        scheduled = self.list_scheduled_parent_tasks()
        pending = self.list_pending_parent_tasks()
        completed = self.db.list_tasks(status="Completed", parent_task_id=None)

        # Attach subtasks for richer UI presentation
        for t in scheduled:
            t["sub_tasks"] = self.get_task_children(t["id"])
        for t in pending:
            t["sub_tasks"] = self.get_task_children(t["id"])

        return {
            "scheduled": scheduled,
            "pending": pending,
            "completed": completed,
            "counts": {
                "scheduled": len(scheduled),
                "pending": len(pending),
                "completed": len(completed),
            },
        }

    def apply_review_updates(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Applies evening review actions (completed or rollover)."""
        updated_tasks: List[Dict[str, Any]] = []

        for item in updates:
            task_id = item.get("task_id")
            if not task_id:
                continue

            current = self.db.get_task(task_id)
            if not current:
                continue

            # Case A: Completed
            if item.get("completed") is True or str(item.get("status")).lower() == "completed":
                up = self.db.update_task(task_id, {
                    "status": "Completed",
                    "remaining_minutes": 0,
                })
                if up:
                    updated_tasks.append(up)
                    # Automatically index completed task into local vector memory
                    try:
                        from src.local_ai.memory import get_memory_manager
                        subtasks = self.get_task_children(task_id)
                        get_memory_manager().index_task(up, subtasks=subtasks)
                    except Exception:
                        pass

            # Case B: Rollover
            elif item.get("remaining_minutes") is not None or str(item.get("status")).lower() in ("pending", "rollover"):
                rem = int(item.get("remaining_minutes") or current.get("remaining_minutes") or 30)
                rollover_count = int(current.get("rollover_count", 0)) + 1
                up = self.db.update_task(task_id, {
                    "status": "Pending",
                    "remaining_minutes": rem,
                    "scheduled_start_at": None,
                    "scheduled_end_at": None,
                    "previous_calendar_event_id": current.get("calendar_event_id"),
                    "calendar_event_id": None,
                    "rollover_count": rollover_count,
                })
                if up:
                    updated_tasks.append(up)

            # Case C: Generic Update
            else:
                up = self.db.update_task(task_id, item)
                if up:
                    updated_tasks.append(up)

        return {"updated": updated_tasks, "count": len(updated_tasks)}

    # Ideas helper
    def log_idea(self, content: str, source: str = "manual") -> Dict[str, Any]:
        return self.db.insert_idea(content=content, source=source)

    def list_unread_ideas(self) -> List[Dict[str, Any]]:
        return self.db.list_ideas(status="Unread")

    def convert_idea_to_plan(self, idea_id: int, parsed_plan: Dict[str, Any]) -> Dict[str, Any]:
        plan_result = self.create_goal_plan(parsed_plan, source="idea")
        self.db.update_idea(idea_id, {"status": "Converted"})
        return plan_result
