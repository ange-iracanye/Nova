"""Free-tier persistence for Nova.

Nova's application code historically stores user state as local JSON/SQLite
files. Free web hosts use ephemeral filesystems, so production can mirror the
small runtime data directory into a free PostgreSQL database without changing
Nova's storage APIs.

When the configured database is unreachable from Render, persistence becomes
best-effort and never prevents authentication or application startup.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import threading
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
except ImportError:  # pragma: no cover
    psycopg = None
    conninfo_to_dict = None


DATABASE_URL = os.getenv("NOVA_DATABASE_URL", "").strip()


def _database_has_ipv4_route(database_url: str) -> bool:
    """Check DNS suitability without opening a database connection."""
    if conninfo_to_dict is None:
        return False
    try:
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


def _is_ipv4(host: str) -> bool:
    try:
        socket.inet_aton(host)
        return host.count(".") == 3
    except OSError:
        return False


def _resolve_ipv4(host: str, port: Any = None) -> str | None:
    try:
        results = socket.getaddrinfo(
            host,
            int(port or 5432),
            socket.AF_INET,
            socket.SOCK_STREAM,
        )
    except (OSError, ValueError):
        return None
    for result in results:
        address = result[4][0]
        if address:
            return address
    return None


def _connect_postgres(database_url: str, timeout: int = 10):
    """Connect using IPv4 when managed DB DNS exposes unusable IPv6 on Render."""
    if psycopg is None or conninfo_to_dict is None:
        raise RuntimeError("psycopg is not installed")
    params = conninfo_to_dict(database_url)
    host = str(params.get("host", "")).strip()
    if host and not _is_ipv4(host):
        ipv4 = _resolve_ipv4(host, params.get("port"))
        if ipv4:
            params["host"] = ipv4
    params["connect_timeout"] = timeout
    params["sslmode"] = "require"
    return psycopg.connect(**params)


class FreePostgresStore:
    """Small PostgreSQL-backed blob store used to persist Nova runtime files."""

    MAX_FILE_BYTES = 8 * 1024 * 1024
    EXCLUDED_PARTS = {"model", "__pycache__"}
    EXCLUDED_NAMES = {"sessions.sqlite3"}

    def __init__(self, database_url: str | None = None):
        self.database_url = (database_url or DATABASE_URL).strip()
        self.enabled = bool(
            self.database_url
            and psycopg is not None
            and _database_has_ipv4_route(self.database_url)
        )
        self._lock = threading.RLock()
        if self.database_url and not self.enabled:
            print("Nova free persistence disabled: configured PostgreSQL has no IPv4 route.")
        if self.enabled:
            try:
                self._initialize()
            except Exception as error:
                self.enabled = False
                print(f"Nova free persistence disabled: database unavailable ({type(error).__name__}).")

    @contextmanager
    def _connect(self):
        if not self.enabled:
            raise RuntimeError("Free PostgreSQL persistence is unavailable.")
        connection = _connect_postgres(self.database_url, timeout=10)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS nova_runtime_files (
                    path TEXT PRIMARY KEY,
                    content BYTEA NOT NULL,
                    sha256 TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

    @staticmethod
    def _safe_path(root: Path, path: Path) -> str:
        return path.relative_to(root).as_posix()

    def _should_sync(self, path: Path) -> bool:
        if path.name in self.EXCLUDED_NAMES:
            return False
        if any(part in self.EXCLUDED_PARTS for part in path.parts):
            return False
        return path.is_file() and path.stat().st_size <= self.MAX_FILE_BYTES

    def restore(self, root: Path) -> int:
        if not self.enabled:
            return 0
        root.mkdir(parents=True, exist_ok=True)
        restored = 0
        try:
            with self._lock, self._connect() as db:
                rows = db.execute("SELECT path, content FROM nova_runtime_files").fetchall()
                for relative_path, content in rows:
                    target = root / relative_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    temporary = target.with_suffix(target.suffix + ".remote.tmp")
                    temporary.write_bytes(bytes(content))
                    temporary.replace(target)
                    restored += 1
        except Exception as error:
            print(f"Nova free persistence restore warning: {error}")
        return restored

    def sync(self, root: Path) -> int:
        if not self.enabled:
            return 0
        root = root.resolve()
        files: list[tuple[str, bytes, str]] = []
        for path in root.rglob("*"):
            try:
                if not self._should_sync(path):
                    continue
                content = path.read_bytes()
            except (OSError, ValueError):
                continue
            relative = self._safe_path(root, path)
            digest = hashlib.sha256(content).hexdigest()
            files.append((relative, content, digest))

        if not files:
            return 0

        try:
            with self._lock, self._connect() as db:
                for relative, content, digest in files:
                    db.execute(
                        """
                        INSERT INTO nova_runtime_files(path, content, sha256, updated_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT(path) DO UPDATE SET
                            content = EXCLUDED.content,
                            sha256 = EXCLUDED.sha256,
                            updated_at = EXCLUDED.updated_at
                        """,
                        (relative, content, digest, datetime.now(timezone.utc)),
                    )
        except Exception as error:
            print(f"Nova free persistence sync warning: {error}")
            return 0
        return len(files)

    def health(self) -> dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "configured": bool(self.database_url), "healthy": False}
        try:
            with self._connect() as db:
                db.execute("SELECT 1").fetchone()
            return {"enabled": True, "configured": True, "healthy": True}
        except Exception as error:
            return {
                "enabled": True,
                "configured": True,
                "healthy": False,
                "error": f"{type(error).__name__}: {error}",
            }


class DatabaseSessionStore(MutableMapping[str, dict[str, Any]]):
    """Drop-in dict-like session store backed by the same free PostgreSQL DB."""

    def __init__(self, database_url: str | None = None):
        self.database_url = (database_url or DATABASE_URL).strip()
        self.enabled = bool(self.database_url and psycopg is not None and _database_has_ipv4_route(self.database_url))
        self._lock = threading.RLock()
        if self.enabled:
            self._initialize()

    @contextmanager
    def _connect(self):
        if not self.enabled:
            raise RuntimeError("Free PostgreSQL session persistence is not configured.")
        connection = _connect_postgres(self.database_url, timeout=10)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS nova_sessions (
                    token TEXT PRIMARY KEY,
                    payload JSONB NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            db.execute("CREATE INDEX IF NOT EXISTS nova_sessions_expiry ON nova_sessions(expires_at)")

    def _cleanup(self, db) -> None:
        db.execute("DELETE FROM nova_sessions WHERE expires_at <= NOW()")

    def __getitem__(self, token: str) -> dict[str, Any]:
        with self._lock, self._connect() as db:
            self._cleanup(db)
            row = db.execute("SELECT payload FROM nova_sessions WHERE token = %s", (token,)).fetchone()
            if row is None:
                raise KeyError(token)
            return dict(row[0])

    def __setitem__(self, token: str, value: dict[str, Any]) -> None:
        expires_at = value.get("expires_at")
        with self._lock, self._connect() as db:
            db.execute(
                """
                INSERT INTO nova_sessions(token, payload, expires_at)
                VALUES (%s, %s::jsonb, %s::timestamptz)
                ON CONFLICT(token) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    expires_at = EXCLUDED.expires_at
                """,
                (token, json.dumps(value, ensure_ascii=False), expires_at),
            )

    def __delitem__(self, token: str) -> None:
        with self._lock, self._connect() as db:
            cursor = db.execute("DELETE FROM nova_sessions WHERE token = %s", (token,))
            if cursor.rowcount == 0:
                raise KeyError(token)

    def __iter__(self) -> Iterator[str]:
        with self._lock, self._connect() as db:
            self._cleanup(db)
            rows = db.execute("SELECT token FROM nova_sessions").fetchall()
        return iter([row[0] for row in rows])

    def __len__(self) -> int:
        with self._lock, self._connect() as db:
            self._cleanup(db)
            row = db.execute("SELECT COUNT(*) FROM nova_sessions").fetchone()
            return int(row[0] if row else 0)

    def items(self):
        with self._lock, self._connect() as db:
            self._cleanup(db)
            rows = db.execute("SELECT token, payload FROM nova_sessions").fetchall()
        return [(token, dict(payload)) for token, payload in rows]

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
