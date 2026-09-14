from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from src.local_ai.memory import MemoryManager


@pytest.fixture
def temp_memory():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        manager = MemoryManager(persist_dir=str(Path(tmp_dir) / "chroma_test"))
        yield manager


def test_memory_initialization(temp_memory):
    assert temp_memory.is_available() is True
    stats = temp_memory.get_memory_stats()
    assert stats["available"] is True
    assert stats["total_memories"] == 0


def test_index_and_search_tasks(temp_memory):
    # Index task 1: Backend authentication
    task_1 = {
        "id": 101,
        "content": "Debug Google OAuth token refresh and expiration logic",
        "priority": "High",
        "remaining_minutes": 60,
        "status": "Completed",
    }
    subtasks_1 = [
        {"content": "Inspect token expiry time", "estimated_minutes": 20},
        {"content": "Implement auto-refresh mechanism", "estimated_minutes": 40},
    ]
    success_1 = temp_memory.index_task(task_1, subtasks_1)
    assert success_1 is True

    # Index task 2: Frontend styling
    task_2 = {
        "id": 102,
        "content": "Refactor navigation header styling and animations",
        "priority": "Low",
        "remaining_minutes": 30,
        "status": "Completed",
    }
    success_2 = temp_memory.index_task(task_2)
    assert success_2 is True

    # Check stats
    stats = temp_memory.get_memory_stats()
    assert stats["total_memories"] == 2

    # Query for authentication / OAuth
    results = temp_memory.search_similar_tasks("OAuth and token expired", top_k=2)
    assert len(results) >= 1
    top_result = results[0]
    assert "OAuth" in top_result["summary"]
    assert top_result["metadata"]["task_id"] == 101
    assert top_result["metadata"]["duration"] == 60


def test_empty_search(temp_memory):
    # Search on empty vector database
    results = temp_memory.search_similar_tasks("something random")
    assert results == []

    # Search with empty query text
    results = temp_memory.search_similar_tasks("")
    assert results == []
