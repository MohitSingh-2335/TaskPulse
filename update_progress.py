from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.task_service import TaskService


def run_evening_review():
    service = TaskService()
    scheduled_tasks = service.list_scheduled_parent_tasks()

    if not scheduled_tasks:
        print("No scheduled tasks found to review for today.")
        return

    print("\n🌙 TaskPulse Evening Review")
    print("==================================================")
    print("Update what you accomplished today:\n")

    updates = []
    for task in scheduled_tasks:
        title = task.get("content", "Untitled Task")
        duration = task.get("remaining_minutes") or task.get("estimated_minutes") or 30
        print(f"👉 {title} ({duration} mins)")

        while True:
            response = input("   Did you finish this completely? (y/n): ").strip().lower()
            if response == "y":
                updates.append({"task_id": task["id"], "completed": True, "status": "Completed"})
                print("   ✅ Marked as completed.\n")
                break
            elif response == "n":
                rem_str = input("   How many minutes of work are still left? (e.g. 20): ").strip()
                rem = int(rem_str) if rem_str.isdigit() else 30
                updates.append({"task_id": task["id"], "remaining_minutes": rem, "status": "Pending"})
                print(f"   ⟳ Rolled over {rem} mins to tomorrow.\n")
                break
            print("   Please enter 'y' or 'n'.")

    result = service.apply_review_updates(updates)
    print(f"🎉 Evening review complete! Updated {result.get('count', 0)} tasks.\n")


if __name__ == "__main__":
    run_evening_review()