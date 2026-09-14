from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from src.config import Config

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    timeframe TEXT NOT NULL DEFAULT 'Daily',
    status TEXT NOT NULL DEFAULT 'Planned',
    source TEXT NOT NULL DEFAULT 'api',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

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
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Unread',
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS telemetry_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,
    model TEXT,
    latency_ms REAL NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteAdapter:
    """Zero-configuration local SQLite persistence adapter."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Config.SQLITE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    # --- Goals ---
    def insert_goal(self, title: str, timeframe: str = "Daily", source: str = "api") -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO goals (title, timeframe, status, source, created_at, updated_at)
                VALUES (?, ?, 'Planned', ?, ?, ?)
                """,
                (title, timeframe, source, now, now),
            )
            goal_id = cur.lastrowid
            conn.commit()
            return self.get_goal(goal_id)

    def get_goal(self, goal_id: int) -> Optional[Dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_goals(self) -> List[Dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM goals ORDER BY created_at DESC")
            return [dict(row) for row in cur.fetchall()]

    # --- Tasks ---
    def insert_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now_iso()
        fields = [
            "goal_id", "parent_task_id", "task_kind", "content", "level",
            "estimated_minutes", "remaining_minutes", "execution_order",
            "priority", "priority_rank", "status", "scheduled_start_at",
            "scheduled_end_at", "calendar_event_id", "previous_calendar_event_id",
            "rollover_count", "source", "created_at", "updated_at"
        ]
        values = [
            task_data.get("goal_id"),
            task_data.get("parent_task_id"),
            task_data.get("task_kind", "task"),
            task_data.get("content", "Untitled Task"),
            task_data.get("level", 1),
            task_data.get("estimated_minutes", 30),
            task_data.get("remaining_minutes", 30),
            task_data.get("execution_order", 1),
            task_data.get("priority", "Medium"),
            task_data.get("priority_rank", 2),
            task_data.get("status", "Pending"),
            task_data.get("scheduled_start_at"),
            task_data.get("scheduled_end_at"),
            task_data.get("calendar_event_id"),
            task_data.get("previous_calendar_event_id"),
            task_data.get("rollover_count", 0),
            task_data.get("source", "api"),
            task_data.get("created_at", now),
            task_data.get("updated_at", now),
        ]
        placeholders = ", ".join(["?"] * len(fields))
        col_names = ", ".join(fields)
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(f"INSERT INTO tasks ({col_names}) VALUES ({placeholders})", values)
            task_id = cur.lastrowid
            conn.commit()
            return self.get_task(task_id)

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def update_task(self, task_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not updates:
            return self.get_task(task_id)

        clean_updates = dict(updates)
        clean_updates["updated_at"] = utc_now_iso()
        set_clauses = [f"{k} = ?" for k in clean_updates.keys()]
        values = list(clean_updates.values()) + [task_id]

        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?", values)
            conn.commit()
            return self.get_task(task_id)

    def delete_task(self, task_id: int) -> bool:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cur.rowcount > 0

    def list_tasks(
        self,
        status: Optional[str] = None,
        parent_task_id: Optional[Any] = -1,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: List[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if parent_task_id is None:
            query += " AND parent_task_id IS NULL"
        elif parent_task_id != -1:
            query += " AND parent_task_id = ?"
            params.append(parent_task_id)

        query += " ORDER BY priority_rank ASC, execution_order ASC, id ASC"

        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    # --- Ideas ---
    def insert_idea(self, content: str, source: str = "manual") -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO ideas (content, status, source, created_at, updated_at)
                VALUES (?, 'Unread', ?, ?, ?)
                """,
                (content, source, now, now),
            )
            idea_id = cur.lastrowid
            conn.commit()
            return self.get_idea(idea_id)

    def get_idea(self, idea_id: int) -> Optional[Dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_ideas(self, status: Optional[str] = "Unread") -> List[Dict[str, Any]]:
        query = "SELECT * FROM ideas"
        params: List[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"

        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def update_idea(self, idea_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        clean_updates = dict(updates)
        clean_updates["updated_at"] = utc_now_iso()
        set_clauses = [f"{k} = ?" for k in clean_updates.keys()]
        values = list(clean_updates.values()) + [idea_id]

        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE ideas SET {', '.join(set_clauses)} WHERE id = ?", values)
            conn.commit()
            return self.get_idea(idea_id)

    # --- Telemetry Logs ---
    def log_telemetry(
        self,
        operation: str,
        latency_ms: float,
        model: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = utc_now_iso()
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO telemetry_logs
                (operation, model, latency_ms, prompt_tokens, completion_tokens, status, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (operation, model, latency_ms, prompt_tokens, completion_tokens, status, error_message, now),
            )
            log_id = cur.lastrowid
            conn.commit()
            cur.execute("SELECT * FROM telemetry_logs WHERE id = ?", (log_id,))
            return dict(cur.fetchone())

    def list_telemetry(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM telemetry_logs ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]

    # --- Readiness ---
    def get_readiness(self) -> Dict[str, Any]:
        tables = {}
        with self._connection() as conn:
            cur = conn.cursor()
            for table_name in ("goals", "tasks", "ideas", "telemetry_logs"):
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cur.fetchone()[0]
                    tables[table_name] = f"ok ({count} rows)"
                except Exception as exc:
                    tables[table_name] = f"error: {exc}"

        return {
            "mode": "sqlite",
            "ready": all(v.startswith("ok") for v in tables.values()),
            "path": str(self.db_path),
            "tables": tables,
        }


# Singleton database instance
_db_instance: Optional[SQLiteAdapter] = None

def get_database() -> SQLiteAdapter:
    """Returns the active database adapter (defaults to robust SQLite)."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SQLiteAdapter()
    return _db_instance
