from __future__ import annotations

from src.local_ai.parser import extract_json_payload, parse_brain_dump_heuristically


def test_extract_json_payload():
    raw_with_markdown = """
    ```json
    {
      "goal": {"title": "Test Goal", "timeframe": "Daily"},
      "tasks": []
    }
    ```
    """
    parsed = extract_json_payload(raw_with_markdown)
    assert parsed["goal"]["title"] == "Test Goal"

    raw_plain = '{"goal": {"title": "Plain Goal"}}'
    assert extract_json_payload(raw_plain)["goal"]["title"] == "Plain Goal"


def test_heuristic_parser():
    text = """
    Finish frontend redesign
    Fix database connection bug for 45 mins urgent
    Research AI models for 1 hour
    Update README for 15m
    """
    result = parse_brain_dump_heuristically(text)
    assert "goal" in result
    assert result["goal"]["title"] == "Finish frontend redesign"

    tasks = result["tasks"]
    assert len(tasks) == 3

    # Check task 1: 45 mins urgent
    assert tasks[0]["estimated_minutes"] == 45
    assert tasks[0]["priority"] == "High"

    # Check task 2: 1 hour -> 60 mins
    assert tasks[1]["estimated_minutes"] == 60

    # Check task 3: 15 mins
    assert tasks[2]["estimated_minutes"] == 15
