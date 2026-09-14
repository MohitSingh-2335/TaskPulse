from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from src.core.database import SQLiteAdapter
from src.core.task_service import TaskService, normalize_priority


@pytest.fixture
def service():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = SQLiteAdapter(db_path=Path(tmp_dir) / "test_svc.db")
        yield TaskService(db=db)


def test_normalize_priority():
    assert normalize_priority("high") == {"rank": 1, "label": "High"}
    assert normalize_priority("Medium") == {"rank": 2, "label": "Medium"}
    assert normalize_priority("low") == {"rank": 3, "label": "Low"}
    assert normalize_priority(1) == {"rank": 1, "label": "High"}
    assert normalize_priority(None) == {"rank": 2, "label": "Medium"}


def test_create_goal_plan(service):
    plan_payload = {
        "goal": {"title": "Ship v1.0", "timeframe": "Daily"},
        "tasks": [
            {
                "content": "Core feature implementation",
                "estimated_minutes": 60,
                "priority": "High",
                "sub_tasks": [
                    {"content": "Database schema migration", "estimated_minutes": 20},
                    {"content": "Service tests", "estimated_minutes": 30},
                ],
            }
        ],
    }

    result = service.create_goal_plan(plan_payload)
    assert result["goal"]["title"] == "Ship v1.0"
    assert result["counts"]["tasks"] == 1
    assert result["counts"]["sub_tasks"] == 2

    # Check pending list
    pending = service.list_pending_parent_tasks()
    assert len(pending) == 1
    assert pending[0]["content"] == "Core feature implementation"


def test_schedule_tasks_flow(service):
    service.create_goal_plan({
        "goal": {"title": "Daily Goal"},
        "tasks": [
            {"content": "Task 1", "estimated_minutes": 30, "priority": "High"},
            {"content": "Task 2", "estimated_minutes": 45, "priority": "Medium"},
        ],
    })

    schedule_res = service.schedule_pending_tasks(
        calendar_service=None,  # Offline virtual schedule test
        start_hour=8,
        buffer_minutes=15,
        timezone_name="UTC",
    )

    assert schedule_res["count"] == 2
    assert len(schedule_res["scheduled"]) == 2

    item1 = schedule_res["scheduled"][0]
    item2 = schedule_res["scheduled"][1]

    assert "08:00:00" in item1["start_at"]
    assert "08:30:00" in item1["end_at"]
    # Task 2 should start after 15 min buffer -> 08:45:00
    assert "08:45:00" in item2["start_at"]


def test_review_and_rollover(service):
    plan = service.create_goal_plan({
        "goal": {"title": "Goal Review"},
        "tasks": [
            {"content": "Completed Task", "estimated_minutes": 30, "status": "Scheduled"},
            {"content": "Rollover Task", "estimated_minutes": 60, "status": "Scheduled"},
        ],
    })
    tasks = plan["tasks"]
    task_comp_id = tasks[0]["id"]
    task_roll_id = tasks[1]["id"]

    updates = [
        {"task_id": task_comp_id, "completed": True},
        {"task_id": task_roll_id, "remaining_minutes": 25, "status": "Pending"},
    ]

    res = service.apply_review_updates(updates)
    assert res["count"] == 2

    t1 = service.db.get_task(task_comp_id)
    t2 = service.db.get_task(task_roll_id)

    assert t1["status"] == "Completed"
    assert t1["remaining_minutes"] == 0

    assert t2["status"] == "Pending"
    assert t2["remaining_minutes"] == 25
    assert t2["rollover_count"] == 1
