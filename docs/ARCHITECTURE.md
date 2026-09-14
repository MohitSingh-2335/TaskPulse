# TaskPulse Architecture & Technical Specification

> **TaskPulse**: Self-hosted, privacy-first task automation engine powered by local/cloud AI classification, Google Calendar sync, and real-time telemetry observability.

---

## 1. System Overview

TaskPulse combines two complementary systems:
1. **Dynamic Daily Task Engine**: Scheduling algorithms, Google Calendar OAuth integration, task decomposition, and evening review/rollover state machines.
2. **Observable Local AI**: Local LLM inference, structured brain dump parsing, voice transcription, and latency/token telemetry tracking.

```
+-----------------------------------------------------------------------------------+
|                                TASKPULSE SYSTEM                                   |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Web UI Dashboard ]   <----->  [ REST API Layer ]  <----->  [ Task Service ]    |
|  - Brain Dump Intake             - Flask Endpoints            - Hierarchy Engine  |
|  - Voice Dictation               - CORS Enabled               - Slot Calculator   |
|  - Calendar Timeline             - Health / Readiness         - Review / Rollover |
|  - Evening Review Hub                                                             |
|  - Telemetry Dashboard                                                            |
|                                                                                   |
+---------------------------+-----------------------------------+-------------------+
                            |                                   |
                            v                                   v
             [ Local AI & Observability ]              [ Dual-Mode Storage ]
             - Local LLM / Ollama                      - Local SQLite (Default)
             - Groq Free-Tier Fallback                   - Zero-cost & offline
             - Rule-based Heuristic Fallback           - Supabase PostgreSQL
             - Telemetry Logger (Latency, Tokens)        - Cloud sync if active
                            |                                   |
                            +-----------------+-----------------+
                                              |
                                              v
                                   [ External Integrations ]
                                   - Google Calendar API (v3)
                                   - Google OAuth2 Flow
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Modules

### `src/config.py`
Central configuration manager. Automatically parses `.env` without external dependencies if needed. Provides strict typing and defaults for:
- `DATABASE_MODE`: `sqlite` (default) or `supabase`
- `SQLITE_PATH`: Local database filepath (`data/task_engine.db`)
- `DEFAULT_TIME_ZONE`: `Asia/Kolkata`
- `SCHEDULE_START_HOUR`: `7` (7:00 AM)
- `SCHEDULE_BUFFER_MINUTES`: `15` (15 mins buffer between scheduled tasks)
- `AI_PROVIDER`: `auto` (tries Local -> Groq -> Heuristic), `local`, or `groq`

### `src/core/database.py`
Abstracts data access into a unified interface `DatabaseAdapter`.
- **SQLiteAdapter**: Built-in Python `sqlite3`, thread-safe connection pooling, zero-install, zero-cost.
- **SupabaseAdapter**: Connects to Supabase PostgreSQL when enabled.
- Automatic table creation and schema migration on startup.

### `src/core/task_service.py`
Domain logic orchestrator:
- **Intake**: Inserts Goal, hierarchical Tasks (Level 1), and Subtasks (Level 2).
- **Scheduling**: Calculates tomorrow's start/end timestamps beginning at `SCHEDULE_START_HOUR`, tagging priority 1 tasks as `[Deep Work]` with color ID 11.
- **Review & Rollover**: Updates task completion status or increments `rollover_count`, detaches previous calendar event IDs, and reschedules for tomorrow.

### `src/core/calendar_sync.py`
Handles Google Calendar OAuth2 authentication:
- Supports desktop local flow (`credentials.json` and `token.json`).
- Supports headless/serverless string environment variables (`GOOGLE_CREDENTIALS_JSON`, `GOOGLE_TOKEN_JSON`).
- Inserts formatted calendar events with checklists.

### `src/local_ai/`
- `engine.py`: Unified AI model orchestrator.
- `parser.py`: Transforms free-form text or voice transcripts into structured JSON plans.
- `telemetry.py`: Records operation latency (ms), token estimates, model metadata, and health stats into the database.

---

## 3. Storage Model

### Tables:
- **`goals`**: `id`, `title`, `timeframe`, `status`, `source`, `created_at`, `updated_at`
- **`tasks`**: `id`, `goal_id`, `parent_task_id`, `task_kind`, `content`, `level`, `estimated_minutes`, `remaining_minutes`, `execution_order`, `priority`, `priority_rank`, `status`, `scheduled_start_at`, `scheduled_end_at`, `calendar_event_id`, `previous_calendar_event_id`, `rollover_count`, `source`, `created_at`, `updated_at`
- **`ideas`**: `id`, `content`, `status`, `source`, `created_at`, `updated_at`
- **`telemetry_logs`**: `id`, `operation`, `model`, `latency_ms`, `prompt_tokens`, `completion_tokens`, `status`, `error_message`, `created_at`
