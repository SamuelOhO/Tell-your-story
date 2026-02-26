import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..config import get_settings

settings = get_settings()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                summary TEXT DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        conn.commit()


def create_session() -> str:
    session_id = str(uuid.uuid4())
    now = _utc_now_iso()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions(id, created_at, updated_at, summary) VALUES (?, ?, ?, ?)",
            (session_id, now, now, ""),
        )
        conn.commit()
    return session_id


def session_exists(session_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return bool(row)


def ensure_session(session_id: str | None) -> str:
    if not session_id:
        return create_session()
    with _connect() as conn:
        row = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row:
            return session_id
    return create_session()


def append_message(session_id: str, role: str, text: str) -> None:
    now = _utc_now_iso()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages(session_id, role, text, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, text, now),
        )
        conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        conn.commit()


def list_messages(session_id: str) -> list[dict[str, str]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, text FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,)
        ).fetchall()
    return [{"role": row["role"], "text": row["text"]} for row in rows]


def list_recent_messages(session_id: str, limit: int) -> list[dict[str, str]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, text FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    rows = list(reversed(rows))
    return [{"role": row["role"], "text": row["text"]} for row in rows]


def count_messages(session_id: str) -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM messages WHERE session_id = ?", (session_id,)).fetchone()
    return int(row["count"] if row else 0)


def get_summary(session_id: str) -> str:
    with _connect() as conn:
        row = conn.execute("SELECT summary FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return str(row["summary"] if row else "")


def update_summary(session_id: str, summary: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE sessions SET summary = ?, updated_at = ? WHERE id = ?",
            (summary, _utc_now_iso(), session_id),
        )
        conn.commit()


def save_draft(session_id: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO drafts(session_id, content, created_at) VALUES (?, ?, ?)",
            (session_id, content, _utc_now_iso()),
        )
        conn.commit()


def get_latest_draft(session_id: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT content FROM drafts
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
    if not row:
        return None
    return str(row["content"])


init_db()
