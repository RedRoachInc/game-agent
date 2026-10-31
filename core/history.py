"""Persistent, per-project agent command history using the Python standard library."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "history.db"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=15)
    try:
        conn.execute("PRAGMA busy_timeout=15000")
        conn.execute("""CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project TEXT NOT NULL,
            profile TEXT NOT NULL,
            agent TEXT NOT NULL,
            task TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('running','completed','failed','interrupted')),
            started_at TEXT NOT NULL,
            finished_at TEXT,
            result TEXT,
            error TEXT
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_commands_project ON commands(project, id DESC)")
        conn.commit()
        yield conn
        conn.commit()
    finally:
        conn.close()


def start(project: str, profile: str, agent: str, task: str) -> int:
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO commands(project,profile,agent,task,status,started_at) VALUES(?,?,?,?,?,?)",
            (project, profile, agent, task, "running", now()),
        )
        return cursor.lastrowid


def finish(command_id: int, status: str, result=None, error: str | None = None) -> None:
    if status not in ("completed", "failed", "interrupted"):
        raise ValueError("Invalid terminal status")
    if result is not None and not isinstance(result, str):
        result = json.dumps(result, ensure_ascii=False, default=str)
    with connect() as conn:
        conn.execute(
            "UPDATE commands SET status=?, finished_at=?, result=?, error=? WHERE id=?",
            (status, now(), result, error, command_id),
        )


def recent(project: str, limit: int = 15) -> list[dict]:
    with connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM commands WHERE project=? ORDER BY id DESC LIMIT ?",
            (project, max(1, min(limit, 100))),
        ).fetchall()
        return [dict(row) for row in rows]
