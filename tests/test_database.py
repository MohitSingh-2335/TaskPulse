from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from src.core.database import SQLiteAdapter


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        yield SQLiteAdapter(db_path=db_path)


def test_goal_crud(temp_db):
    goal = temp_db.insert_goal(title="Test Sprint Goal", timeframe="Weekly")
    assert goal["id"] is not None
    assert goal["title"] == "Test Sprint Goal"
    assert goal["timeframe"] == "Weekly"

    fetched = temp_db.get_goal(goal["id"])
    assert fetched["id"] == goal["id"]

    all_goals = temp_db.list_goals()
    assert len(all_goals) == 1


def test_task_crud(temp_db):
    goal = temp_db.insert_goal(title="Goal 1")
    task = temp_db.insert_task({
        "goal_id": goal["id"],
        "content": "Write unit tests",
        "estimated_minutes": 45,
        "priority": "High",
        "priority_rank": 1,
    })
    assert task["id"] is not None
    assert task["content"] == "Write unit tests"
    assert task["estimated_minutes"] == 45
    assert task["priority_rank"] == 1

    # Update task
    updated = temp_db.update_task(task["id"], {"status": "Scheduled", "remaining_minutes": 20})
    assert updated["status"] == "Scheduled"
    assert updated["remaining_minutes"] == 20

    # List tasks
    scheduled_tasks = temp_db.list_tasks(status="Scheduled")
    assert len(scheduled_tasks) == 1


def test_idea_crud(temp_db):
    idea = temp_db.insert_idea(content="Build an automated workflow")
    assert idea["id"] is not None
    assert idea["status"] == "Unread"

    ideas = temp_db.list_ideas(status="Unread")
    assert len(ideas) == 1

    temp_db.update_idea(idea["id"], {"status": "Converted"})
    unread = temp_db.list_ideas(status="Unread")
    assert len(unread) == 0


def test_telemetry_logging(temp_db):
    log = temp_db.log_telemetry(
        operation="test_op",
        model="test-model",
        latency_ms=12.5,
        prompt_tokens=10,
        completion_tokens=20,
    )
    assert log["id"] is not None
    assert log["latency_ms"] == 12.5

    logs = temp_db.list_telemetry()
    assert len(logs) == 1
