-- ==========================================================
-- TaskPulse: Canonical Database Schema
-- Compatible with SQLite & PostgreSQL (Supabase)
-- ==========================================================

-- 1. Goals Table
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    timeframe TEXT NOT NULL DEFAULT 'Daily',
    status TEXT NOT NULL DEFAULT 'Planned',
    source TEXT NOT NULL DEFAULT 'api',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tasks Table (Hierarchical tasks and subtasks)
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    task_kind TEXT NOT NULL DEFAULT 'task',
    content TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    estimated_minutes INTEGER NOT NULL DEFAULT 30,
    remaining_minutes INTEGER NOT NULL DEFAULT 30,
    execution_order INTEGER NOT NULL DEFAULT 1,
    priority TEXT NOT NULL DEFAULT 'Medium',
    priority_rank INTEGER NOT NULL DEFAULT 2,
    status TEXT NOT NULL DEFAULT 'Pending',
    scheduled_start_at TEXT,
    scheduled_end_at TEXT,
    calendar_event_id TEXT,
    previous_calendar_event_id TEXT,
    rollover_count INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'api',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Ideas Table (Quick Capture Inbox)
CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Unread',
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Telemetry Logs Table (Local Observability)
CREATE TABLE IF NOT EXISTS telemetry_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,
    model TEXT,
    latency_ms REAL NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Helpful Indices for High Performance
CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status);
