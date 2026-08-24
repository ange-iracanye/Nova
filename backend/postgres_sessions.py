from __future__ import annotations

import json
import socket
import threading
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.conninfo import conninfo_to_dict


def _connect_postgres(database_url: str, timeout: int = 8):
    """Connect to PostgreSQL while preferring IPv4 on hosts with broken IPv6 routing.

    Render instances can resolve a managed PostgreSQL hostname to an IPv6 address
    even when the instance has no usable IPv6 route. Resolve an IPv4 address and
    pass the parsed connection parameters to psycopg so the database URL itself
    does not need to be changed.
    """
    params = conninfo_to_dict(database_url)
    host = str(params.get("host", "")).strip()
    if host and not _is_ipv4(host):
        ipv4 = _resolve_ipv4(host, params.get("port"))
        if ipv4:
            params["host"] = ipv4
    params["connect_timeout"] = timeout
    params["sslmode"] = "require"
    return psycopg.connect(**params)


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


class PostgresSessionStore:
    """PostgreSQL-backed session mapping for production deployments."""

    def __init__(self, database_url: str) -> None:
        if not database_url:
            raise RuntimeError("NOVA_DATABASE_URL is required for PostgreSQL sessions.")
        self.database_url = database_url
        self._lock = threading.RLock()
        self._initialized = False

    def _raw_connect(self):
        return _connect_postgres(self.database_url, timeout=8)

    def _initialize(self) -> None:
        with self._lock, self._raw_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS nova_sessions (
                        token TEXT PRIMARY KEY,
                        email TEXT NOT NULL,
                        payload JSONB NOT NULL,
                        expires_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_nova_sessions_expires ON nova_sessions(expires_at)"
                )
            conn.commit()
        self._initialized = True

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._lock:
            if not self._initialized:
                self._initialize()

    def _connect(self):
        self._ensure_initialized()
        return self._raw_connect()

    def _cleanup(self, conn) -> None:
        conn.execute("DELETE FROM nova_sessions WHERE expires_at <= NOW()")

    def __setitem__(self, token: str, value: dict[str, Any]) -> None:
        expires_at = str(value.get("expires_at", ""))
        email = str(value.get("email", "")).strip().lower()
        if not token or not email or not expires_at:
            raise ValueError("Session requires token, email and expires_at.")
        with self._lock, self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO nova_sessions(token, email, payload, expires_at)
                    VALUES (%s, %s, %s::jsonb, %s::timestamptz)
                    ON CONFLICT(token) DO UPDATE SET
                        email = EXCLUDED.email,
                        payload = EXCLUDED.payload,
                        expires_at = EXCLUDED.expires_at
                    """,
                    (token, email, json.dumps(value), expires_at),
                )
            conn.commit()

    def __getitem__(self, token: str) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            self._cleanup(conn)
            row = conn.execute(
                "SELECT payload FROM nova_sessions WHERE token = %s",
                (token,),
            ).fetchone()
            conn.commit()
        if row is None:
            raise KeyError(token)
        return dict(row[0])

    def __delitem__(self, token: str) -> None:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM nova_sessions WHERE token = %s",
                (token,),
            )
            conn.commit()
        if cur.rowcount == 0:
            raise KeyError(token)

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

    def items(self):
        with self._lock, self._connect() as conn:
            self._cleanup(conn)
            rows = conn.execute(
                "SELECT token, payload FROM nova_sessions"
            ).fetchall()
            conn.commit()
        return [(token, dict(payload)) for token, payload in rows]

    def __iter__(self):
        return iter([token for token, _ in self.items()])

    def __len__(self) -> int:
        with self._lock, self._connect() as conn:
            self._cleanup(conn)
            row = conn.execute(
                "SELECT COUNT(*) FROM nova_sessions"
            ).fetchone()
            conn.commit()
        return int(row[0] if row else 0)

    def delete_user_sessions(self, email: str) -> int:
        normalized = str(email).strip().lower()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM nova_sessions WHERE email = %s",
                (normalized,),
            )
            conn.commit()
        return int(cur.rowcount or 0)
