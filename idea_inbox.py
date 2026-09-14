from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.task_service import TaskService


def log_idea(text: str):
    service = TaskService()
    idea = service.log_idea(text, source="cli_idea_inbox")
    print(f"[IDEA] Idea captured: [{idea.get('id')}] {idea.get('content')}")


def view_ideas():
    service = TaskService()
    ideas = service.list_unread_ideas()
    if not ideas:
        print("Your idea inbox is empty.")
        return

    print(f"\n[IDEA] Your Unread Ideas ({len(ideas)}):")
    for idea in ideas:
        print(f"  [{idea.get('id')}] {idea.get('created_at')[:16]} - {idea.get('content')}")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_idea(" ".join(sys.argv[1:]))
    else:
        view_ideas()