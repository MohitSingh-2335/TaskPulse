# Dynamic Daily Task Engine (TaskPulse)

A local-first task engine that converts unstructured text and voice notes into prioritized daily schedules with Google Calendar synchronization and local vector memory.

## Overview

Translating raw thoughts and voice notes into an actionable schedule requires manual task breakdown, realistic duration estimates, and calendar coordination. TaskPulse parses free-form text or voice input into structured goal and subtask hierarchies using a tiered AI pipeline (local Ollama, Groq Cloud API, or offline regex heuristics), calibrates estimates using historical completion patterns retrieved from ChromaDB, and schedules non-overlapping time blocks in Google Calendar. The automated test suite achieves a 100% pass rate across 19 unit and integration tests.

## Results

| Metric | Value | Dataset and Size | How Measured | Source File |
|---|---|---|---|---|
| Automated Test Pass Rate | 100% (19 passed) | 19 test functions across 5 test files | `pytest -v` unit and integration assertions | `tests/` |
| Heuristic Parsing Accuracy | Exact duration & priority extraction | 4 multi-line task strings with duration units | Regex pattern matching (`mins`, `hours`, priority terms) | `src/local_ai/parser.py`, `tests/test_ai_parser.py` |
| Semantic Memory Retrieval | Top-1 match (`task_id: 101`, 60m duration) | 2 indexed tasks with subtask structures | ChromaDB cosine similarity query on "OAuth and token expired" | `src/local_ai/memory.py`, `tests/test_memory.py` |
| Schedule Arithmetic Precision | 0 ms overlap (+15 min buffer) | 2-task pending queue (30m, 45m) | Datetime calculation starting at `SCHEDULE_START_HOUR` | `src/core/task_service.py`, `tests/test_task_service.py` |
| Telemetry Tracking | Latency (ms), token usage, status | 13 runtime execution traces | `time.perf_counter()` context manager logged to SQLite | `src/local_ai/telemetry.py`, `data/task_engine.db` |

## How It Works

1. **Intake**: Raw text or audio memos enter via the web interface or `POST /api/intake`.
2. **Context Retrieval**: `AIEngine` queries ChromaDB for the 3 most semantically similar past tasks to provide historical duration and priority context.
3. **Decomposition**: The engine routes through local Ollama (`llama3:8b`), Groq API (`llama-3.3-70b-versatile`), or an offline regex heuristic parser to generate structured JSON plans.
4. **Persistence & Observability**: Goals, Level-1 tasks, and Level-2 subtasks are stored in SQLite (`data/task_engine.db`), while `TelemetryTracker` records inference latency in milliseconds and token counts.
5. **Time-Blocking**: `TaskService` calculates chronological slots for tomorrow starting at 07:00 AM with 15-minute buffers, creating events in an isolated Google Calendar ("TaskPulse") so primary calendars remain untouched.
6. **Review & Rollover**: Completed tasks are auto-indexed into ChromaDB for future retrieval, while incomplete tasks roll over with incremented rollover counts.

## Features

- **Cascading AI Decomposition**: Parses raw text into goals, tasks, and subtasks using Ollama, Groq, or an offline rule-based heuristic fallback.
- **Local RAG Task Memory**: Indexes completed tasks into ChromaDB vector storage to ground future task planning on past completion history.
- **Isolated Calendar Time-Blocking**: Automatically formats and schedules tasks into a dedicated "TaskPulse" Google Calendar without altering primary calendar events.
- **Evening Review & Rollover**: Tracks daily execution, increments rollover counters for unfinished work, and preserves remaining minute estimates.
- **Real-Time Telemetry**: Automatically records operation latency (ms), token usage, and error status for every pipeline execution into SQLite.

## Tech Stack

Python, Flask, SQLite, ChromaDB, Groq API, Google Calendar API, Pytest

## Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/MohitSingh-2335/Dynamic-Daily-Task-Engine.git
cd Dynamic-Daily-Task-Engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (optional, defaults to local SQLite and heuristic parser)
cp .env.example .env

# 4. Start the application server
python run.py

# 5. Open the web dashboard
# Navigate to http://127.0.0.1:5000 in your browser
```

## Tests

19 test functions across 5 test files covering database operations, task service scheduling, AI parsing, ChromaDB vector memory, and REST API routes.

```bash
pytest tests/ -v
```

## Project Structure

- `api/` - Vercel serverless functions and backward-compatibility entrypoints.
- `data/` - Local SQLite database (`task_engine.db`) and ChromaDB vector persistence files.
- `docs/` - System architecture specification, database schemas, and merge blueprints.
- `src/` - Application source code (Flask app, config, domain services, local AI, and web UI).
- `tests/` - Automated unit and integration test suite.

## Limitations

- Audio transcription via local Whisper requires the optional `openai-whisper` package or browser Web Speech API.
- Google Calendar synchronization requires OAuth desktop credentials (`credentials.json`) from Google Cloud Console.
- Cloud LLM acceleration requires a valid `GROQ_API_KEY` (system defaults to the offline heuristic parser if omitted).

## License

This project is open-source under the MIT License.

---

Mohit Singh | [GitHub](https://github.com/MohitSingh-2335) | [LinkedIn](https://www.linkedin.com/in/mohit-singh-172548253/) | [Portfolio](https://mohitsingh-2335.github.io/)
