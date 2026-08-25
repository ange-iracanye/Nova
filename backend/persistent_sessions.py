from __future__ import annotations

import json
import os
import socket
import sqlite3
import threading
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _database_has_ipv4_route(database_url: str) -> bool:
    """Return whether the configured PostgreSQL host has an IPv4 address."""
    try:
        from psycopg.conninfo import conninfo_to_dict

        params = conninfo_to_dict(database_url)
        host = str(params.get("host", "")).strip()
        if not host:
            return False
        try:
            socket.inet_aton(host)
            return True
        except OSError:
            pass
        results = socket.getaddrinfo(
            host,
            int(params.get("port") or 5432),
            socket.AF_INET,
            socket.SOCK_STREAM,
        )
        return any(result[4][0] for result in results)
    except (OSError, ValueError, TypeError):
        return False


class PersistentSessionStore(MutableMapping[str, dict[str, Any]]):
    """Persistent sessions with PostgreSQL support and a safe SQLite fallback.

    Render free web instances can resolve some managed PostgreSQL endpoints to
    IPv6 even though the instance has no IPv6 route. Authentication must remain
    usable in that situation, so an IPv6-only DB configuration does not get
    selected as the session backend.
    """

    def __new__(cls, path: str | None = None):
        if cls is PersistentSessionStore:
            environment = os.getenv("NOVA_ENV", "development").strip().lower()
            database_url = os.getenv("NOVA_DATABASE_URL", "").strip()
            explicit_path = str(path or "").strip()
            default_sqlite_paths = {
                "data/sessions.sqlite3",
                str(Path(os.getenv("NOVA_DATA_DIR", "data")) / "sessions.sqlite3"),
            }

            if environment == "production" and database_url and (
                not explicit_path or explicit_path in default_sqlite_paths
            ):
                if _database_has_ipv4_route(database_url):
                    from backend.postgres_sessions import PostgresSessionStore
                    return PostgresSessionStore(database_url)

            if explicit_path.startswith(("postgresql://", "postgres://")):
                if _database_has_ipv4_route(explicit_path):
                    from backend.postgres_sessions import PostgresSessionStore
                    return PostgresSessionStore(explicit_path)
                path = None

        return super().__new__(cls)

    def __init__(self, path: str | None = None) -> None:
        configured = path or os.getenv("NOVA_SESSION_DB", "data/sessions.sqlite3")
        if str(configured).startswith(("postgresql://", "postgres://")):
            configured = "data/sessions.sqlite3"
        self.path = Path(configured)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._db() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)")

    def _cleanup(self, db: sqlite3.Connection) -> None:
        now = datetime.now(timezone.utc).isoformat()
        db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))

    def __getitem__(self, token: str) -> dict[str, Any]:
        with self._lock, self._db() as db:
            self._cleanup(db)
            row = db.execute("SELECT payload FROM sessions WHERE token = ?", (token,)).fetchone()
            if row is None:
                raise KeyError(token)
            return json.loads(row[0])

    def __setitem__(self, token: str, value: dict[str, Any]) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        expires_at = str(value.get("expires_at", ""))
        with self._lock, self._db() as db:
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
        with self._lock, self._db() as db:
            cursor = db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            if cursor.rowcount == 0:
                raise KeyError(token)

    def __iter__(self) -> Iterator[str]:
        with self._lock, self._db() as db:
            self._cleanup(db)
            rows = db.execute("SELECT token FROM sessions").fetchall()
        return iter([row[0] for row in rows])

    def __len__(self) -> int:
        with self._lock, self._db() as db:
            self._cleanup(db)
            row = db.execute("SELECT COUNT(*) FROM sessions").fetchone()
            return int(row[0] if row else 0)

    def items(self):
        with self._lock, self._db() as db:
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
