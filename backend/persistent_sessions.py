from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import MutableMapping, Iterator
from typing import Any


class PersistentSessionStore(MutableMapping[str, dict[str, Any]]):
    """Small SQLite-backed mapping for authentication sessions.

    The API layer can keep its existing dict-like session code while sessions
    survive process restarts. The database path is configurable with
    NOVA_SESSION_DB and defaults to data/sessions.sqlite3.
    """

    def __init__(self, path: str | None = None) -> None:
        configured = path or os.getenv("NOVA_SESSION_DB", "data/sessions.sqlite3")
        self.path = Path(configured)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=10,
            check_same_thread=False,
        )
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)"
            )

    def _cleanup(self, db: sqlite3.Connection) -> None:
        now = datetime.now(timezone.utc).isoformat()
        db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))

    def __getitem__(self, token: str) -> dict[str, Any]:
        with self._lock, self._connect() as db:
            self._cleanup(db)
            row = db.execute(
                "SELECT payload FROM sessions WHERE token = ?",
                (token,),
            ).fetchone()
            if row is None:
                raise KeyError(token)
            return json.loads(row[0])

    def __setitem__(self, token: str, value: dict[str, Any]) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        expires_at = str(value.get("expires_at", ""))
        with self._lock, self._connect() as db:
            db.execute(
                """
                INSERT INTO sessions(token, payload, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(token) DO UPDATE SET
                    payload = excluded.payload,
                    expires_at = excluded.expires_at
                """,
                (token, payload, expires_at),
            )

    def __delitem__(self, token: str) -> None:
        with self._lock, self._connect() as db:
            cursor = db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            if cursor.rowcount == 0:
                raise KeyError(token)

    def __iter__(self) -> Iterator[str]:
        with self._lock, self._connect() as db:
            self._cleanup(db)
            rows = db.execute("SELECT token FROM sessions").fetchall()
        return iter([row[0] for row in rows])

    def __len__(self) -> int:
        with self._lock, self._connect() as db:
            self._cleanup(db)
            row = db.execute("SELECT COUNT(*) FROM sessions").fetchone()
            return int(row[0] if row else 0)

    def items(self):
        with self._lock, self._connect() as db:
            self._cleanup(db)
            rows = db.execute("SELECT token, payload FROM sessions").fetchall()
        return [(token, json.loads(payload)) for token, payload in rows]

    def get(self, token: str, default=None):
        try:
            return self[token]
        except KeyError:
            return default

    def pop(self, token: str, default=None):
        try:
            value = self[token]
        except KeyError:
            return default
        try:
            del self[token]
        except KeyError:
            pass
        return value
