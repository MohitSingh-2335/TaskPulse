from __future__ import annotations

import json
import re
from typing import Any, Dict, List

INTAKE_SYSTEM_PROMPT = """
You are TaskPulse AI, an intelligent daily task decomposition and prioritization engine.
Your task is to analyze the user's raw unstructured text (brain dump or voice notes) and convert it into a well-structured daily action plan.

Rules:
1. Produce ONLY valid JSON with no markdown wrapping or conversational filler.
2. Group the work under a high-level Goal.
3. Decompose the request into individual, actionable Level-1 Tasks.
4. If a task is complex, break it down into Level-2 Subtasks.
5. Estimate realistic durations in minutes (default 30-60 mins for deep work, 15-30 mins for smaller tasks).
6. Assign priority: "High" (deep, cognitively demanding or urgent work), "Medium" (standard daily deliverables), "Low" (quick administrative chores).
7. Sequence the tasks in logical execution order (execution_order: 1, 2, 3...).

Output Schema:
{
  "goal": {
    "title": "String (Concise summary of the overall objective)",
    "timeframe": "Daily"
  },
  "tasks": [
    {
      "content": "String (Actionable task title)",
      "estimated_minutes": 45,
      "priority": "High",
      "execution_order": 1,
      "sub_tasks": [
        {
          "content": "String (Specific subtask)",
          "estimated_minutes": 20,
          "priority": "High"
        }
      ]
    }
  ]
}
""".strip()


def extract_json_payload(raw_text: str) -> Dict[str, Any]:
    """Extracts and parses JSON from raw LLM output, stripping markdown blocks if present."""
    clean = raw_text.strip()
    if "```" in clean:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if match:
            clean = match.group(1).strip()

    return json.loads(clean)


def parse_brain_dump_heuristically(raw_text: str) -> Dict[str, Any]:
    """Zero-dependency, offline rule-based fallback parser for brain dumps."""
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    if not lines:
        return {
            "goal": {"title": "Daily Focus Plan", "timeframe": "Daily"},
            "tasks": [{"content": "Review daily priorities", "estimated_minutes": 30, "priority": "Medium", "execution_order": 1, "sub_tasks": []}]
        }

    # Extract goal title from first line or summary
    goal_title = lines[0].lstrip("#*-0123456789. ")
    if len(goal_title) > 60:
        goal_title = goal_title[:57] + "..."

    task_lines = lines[1:] if len(lines) > 1 else lines
    tasks: List[Dict[str, Any]] = []

    for index, line in enumerate(task_lines, start=1):
        clean_line = line.lstrip("#*-0123456789. ")
        if not clean_line:
            continue

        # Extract duration
        duration = 30
        dur_match = re.search(r"(\d+)\s*(?:mins?|minutes?|m)\b", clean_line, re.IGNORECASE)
        hour_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b", clean_line, re.IGNORECASE)
        if dur_match:
            duration = int(dur_match.group(1))
        elif hour_match:
            duration = int(float(hour_match.group(1)) * 60)

        # Clean duration text from title
        title = re.sub(r"\b(?:for\s*)?\d+\s*(?:mins?|minutes?|hours?|hrs?|h|m)\b", "", clean_line, flags=re.IGNORECASE).strip()
        if not title:
            title = clean_line

        # Extract priority
        priority = "Medium"
        lower = clean_line.lower()
        if any(w in lower for w in ("urgent", "critical", "high", "deep work", "asap", "priority")):
            priority = "High"
        elif any(w in lower for w in ("minor", "low", "quick", "optional", "easy")):
            priority = "Low"

        tasks.append({
            "content": title,
            "estimated_minutes": max(10, duration),
            "priority": priority,
            "execution_order": index,
            "sub_tasks": [],
        })

    if not tasks:
        tasks = [{"content": goal_title, "estimated_minutes": 45, "priority": "Medium", "execution_order": 1, "sub_tasks": []}]

    return {
        "goal": {"title": goal_title or "Daily Focus Plan", "timeframe": "Daily"},
        "tasks": tasks,
    }
