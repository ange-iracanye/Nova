"""Lightweight first-party analytics for Nova.

Analytics intentionally stores only a one-way user key, event type, route and
UTC timestamp. Conversation text, passwords, IP addresses and other request
contents are never persisted here.
"""

from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Request

try:
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
except ImportError:  # pragma: no cover
    psycopg = None
    conninfo_to_dict = None

router = APIRouter()
DATABASE_URL = os.getenv("NOVA_DATABASE_URL", "").strip()
ADMIN_EMAILS = {
    value.strip().lower()
    for value in os.getenv("NOVA_ANALYTICS_ADMIN_EMAILS", "").split(",")
    if value.strip()
}
TRACKED_PREFIXES = (
    "/chat", "/dashboard", "/settings", "/study", "/upload", "/conversation"
)


def _user_key(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _connect():
    if psycopg is None or conninfo_to_dict is None or not DATABASE_URL:
        raise RuntimeError("Nova analytics database is not configured.")
    params = conninfo_to_dict(DATABASE_URL)
    params["connect_timeout"] = 8
    params["sslmode"] = "require"
    return psycopg.connect(**params)


def initialize() -> None:
    if not DATABASE_URL or psycopg is None:
        return
    try:
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nova_analytics_events (
                    id BIGSERIAL PRIMARY KEY,
                    user_key TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS nova_analytics_events_created ON nova_analytics_events(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS nova_analytics_events_user_created ON nova_analytics_events(user_key, created_at)"
            )
            conn.commit()
    except Exception as exc:
        print(f"Nova analytics initialization warning: {type(exc).__name__}: {exc}", flush=True)


def record_event(email: str, event_type: str, path: str) -> None:
    if not DATABASE_URL or not email or psycopg is None:
        return
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO nova_analytics_events(user_key, event_type, path) VALUES (%s, %s, %s)",
                (_user_key(email), event_type[:80], path[:300]),
            )
            conn.commit()
    except Exception as exc:
        print(f"Nova analytics event warning: {type(exc).__name__}: {exc}", flush=True)


def _authorized_email(request: Request) -> str:
    from backend import api
    session = api.get_auth_session(request)
    email = str(session.get("email", "")).strip().lower() if isinstance(session, dict) else ""
    if not email:
        raise HTTPException(status_code=401, detail="A valid Nova session is required.")
    if not ADMIN_EMAILS or email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Analytics access is restricted to Nova administrators.")
    return email


def _summary(days: int) -> dict[str, Any]:
    days = max(1, min(days, 365))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with _connect() as conn:
        total_users = int(conn.execute("SELECT COUNT(*) FROM nova_users").fetchone()[0])
        events = conn.execute(
            """
            SELECT created_at::date AS day, COUNT(*) AS events,
                   COUNT(DISTINCT user_key) AS users
            FROM nova_analytics_events
            WHERE created_at >= %s
            GROUP BY created_at::date
            ORDER BY day
            """,
            (cutoff,),
        ).fetchall()
        dau = int(conn.execute(
            "SELECT COUNT(DISTINCT user_key) FROM nova_analytics_events WHERE created_at >= NOW() - INTERVAL '1 day'"
        ).fetchone()[0])
        wau = int(conn.execute(
            "SELECT COUNT(DISTINCT user_key) FROM nova_analytics_events WHERE created_at >= NOW() - INTERVAL '7 days'"
        ).fetchone()[0])
        mau = int(conn.execute(
            "SELECT COUNT(DISTINCT user_key) FROM nova_analytics_events WHERE created_at >= NOW() - INTERVAL '30 days'"
        ).fetchone()[0])
        total_events = int(conn.execute(
            "SELECT COUNT(*) FROM nova_analytics_events WHERE created_at >= %s", (cutoff,)
        ).fetchone()[0])
        chat_events = int(conn.execute(
            "SELECT COUNT(*) FROM nova_analytics_events WHERE event_type = 'chat' AND created_at >= %s", (cutoff,)
        ).fetchone()[0])
        returning = int(conn.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT user_key FROM nova_analytics_events
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY user_key HAVING COUNT(DISTINCT created_at::date) > 1
            ) active
            """
        ).fetchone()[0])
        event_types = conn.execute(
            """
            SELECT event_type, COUNT(*) FROM nova_analytics_events
            WHERE created_at >= %s GROUP BY event_type ORDER BY COUNT(*) DESC LIMIT 10
            """,
            (cutoff,),
        ).fetchall()
    return {
        "registered_users": total_users,
        "active_today": dau,
        "active_week": wau,
        "active_month": mau,
        "returning_users_30d": returning,
        "events": total_events,
        "chat_requests": chat_events,
        "days": days,
        "daily": [
            {"date": row[0].isoformat(), "events": int(row[1]), "users": int(row[2])}
            for row in events
        ],
        "event_types": [{"event": row[0], "count": int(row[1])} for row in event_types],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/analytics")
def get_analytics(request: Request, days: int = 30):
    _authorized_email(request)
    if not DATABASE_URL or psycopg is None:
        raise HTTPException(status_code=503, detail="Analytics database is not configured.")
    try:
        return {"success": True, "analytics": _summary(days)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Analytics data is temporarily unavailable.") from exc


async def analytics_middleware(request: Request, call_next):
    """Record authenticated product usage without storing request contents."""
    response = await call_next(request)
    try:
        if request.url.path.startswith(TRACKED_PREFIXES):
            from backend import api
            session = api.get_auth_session(request)
            email = str(session.get("email", "")).strip().lower() if isinstance(session, dict) else ""
            if email:
                path = request.url.path
                if path.startswith("/chat"):
                    event = "chat"
                elif path.startswith("/dashboard"):
                    event = "dashboard"
                elif path.startswith("/settings"):
                    event = "settings"
                elif path.startswith("/study"):
                    event = "study"
                elif path.startswith("/upload"):
                    event = "upload"
                else:
                    event = "conversation"
                record_event(email, event, path)
    except Exception:
        pass
    return response


initialize()
