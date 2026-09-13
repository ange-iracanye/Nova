"""Lightweight first-party owner analytics for Nova.

Only anonymous user keys, event names, routes and timestamps are stored here.
No conversation text, passwords, IP addresses or request bodies are persisted.
"""

from __future__ import annotations

import hashlib
import os
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
            conn.execute("CREATE INDEX IF NOT EXISTS nova_analytics_events_created ON nova_analytics_events(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS nova_analytics_events_user_created ON nova_analytics_events(user_key, created_at)")
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


def _empty_summary(days: int) -> dict[str, Any]:
    return {
        "registered_users": 0, "active_today": 0, "active_week": 0, "active_month": 0,
        "returning_users_30d": 0, "events": 0, "chat_requests": 0, "days": days,
        "daily": [], "event_types": [], "routes": [], "hourly": [0] * 24,
        "weekday": [0] * 7, "new_active_users": 0, "avg_events_per_active_user": 0,
        "avg_events_per_day": 0, "peak_day": None, "peak_hour": None,
        "first_event_at": None, "last_event_at": None, "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _summary(days: int) -> dict[str, Any]:
    days = max(1, min(days, 365))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with _connect() as conn:
        total_users = int(conn.execute("SELECT COUNT(*) FROM nova_users").fetchone()[0])
        daily_rows = conn.execute(
            """
            SELECT created_at::date AS day, COUNT(*) AS events, COUNT(DISTINCT user_key) AS users
            FROM nova_analytics_events WHERE created_at >= %s
            GROUP BY created_at::date ORDER BY day
            """, (cutoff,)
        ).fetchall()
        dau = int(conn.execute("SELECT COUNT(DISTINCT user_key) FROM nova_analytics_events WHERE created_at >= NOW() - INTERVAL '1 day'").fetchone()[0])
        wau = int(conn.execute("SELECT COUNT(DISTINCT user_key) FROM nova_analytics_events WHERE created_at >= NOW() - INTERVAL '7 days'").fetchone()[0])
        mau = int(conn.execute("SELECT COUNT(DISTINCT user_key) FROM nova_analytics_events WHERE created_at >= NOW() - INTERVAL '30 days'").fetchone()[0])
        total_events = int(conn.execute("SELECT COUNT(*) FROM nova_analytics_events WHERE created_at >= %s", (cutoff,)).fetchone()[0])
        chat_events = int(conn.execute("SELECT COUNT(*) FROM nova_analytics_events WHERE event_type = 'chat' AND created_at >= %s", (cutoff,)).fetchone()[0])
        returning = int(conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT user_key FROM nova_analytics_events
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY user_key HAVING COUNT(DISTINCT created_at::date) > 1
            ) active
        """).fetchone()[0])
        active_period = int(conn.execute("SELECT COUNT(DISTINCT user_key) FROM nova_analytics_events WHERE created_at >= %s", (cutoff,)).fetchone()[0])
        first_seen_active = int(conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT user_key, MIN(created_at) AS first_seen
                FROM nova_analytics_events GROUP BY user_key
                HAVING MIN(created_at) >= %s
            ) firsts
        """, (cutoff,)).fetchone()[0])
        event_types = conn.execute("SELECT event_type, COUNT(*) FROM nova_analytics_events WHERE created_at >= %s GROUP BY event_type ORDER BY COUNT(*) DESC LIMIT 12", (cutoff,)).fetchall()
        routes = conn.execute("SELECT path, COUNT(*) FROM nova_analytics_events WHERE created_at >= %s GROUP BY path ORDER BY COUNT(*) DESC LIMIT 15", (cutoff,)).fetchall()
        hourly_rows = conn.execute("SELECT EXTRACT(HOUR FROM created_at)::int AS hour, COUNT(*) FROM nova_analytics_events WHERE created_at >= %s GROUP BY hour ORDER BY hour", (cutoff,)).fetchall()
        weekday_rows = conn.execute("SELECT EXTRACT(ISODOW FROM created_at)::int AS weekday, COUNT(*) FROM nova_analytics_events WHERE created_at >= %s GROUP BY weekday ORDER BY weekday", (cutoff,)).fetchall()
        first_event = conn.execute("SELECT MIN(created_at) FROM nova_analytics_events").fetchone()[0]
        last_event = conn.execute("SELECT MAX(created_at) FROM nova_analytics_events").fetchone()[0]

    hourly = [0] * 24
    for hour, count in hourly_rows:
        hourly[int(hour)] = int(count)
    weekday = [0] * 7
    for day, count in weekday_rows:
        weekday[int(day) - 1] = int(count)
    avg_per_user = round(total_events / active_period, 1) if active_period else 0
    avg_per_day = round(total_events / days, 1)
    peak_day = max(daily_rows, key=lambda row: int(row[1]), default=None)
    peak_hour_value = max(enumerate(hourly), key=lambda item: item[1], default=(0, 0))

    return {
        "registered_users": total_users,
        "active_today": dau,
        "active_week": wau,
        "active_month": mau,
        "returning_users_30d": returning,
        "events": total_events,
        "chat_requests": chat_events,
        "days": days,
        "daily": [{"date": row[0].isoformat(), "events": int(row[1]), "users": int(row[2])} for row in daily_rows],
        "event_types": [{"event": row[0], "count": int(row[1])} for row in event_types],
        "routes": [{"path": row[0], "count": int(row[1])} for row in routes],
        "hourly": hourly,
        "weekday": weekday,
        "new_active_users": first_seen_active,
        "avg_events_per_active_user": avg_per_user,
        "avg_events_per_day": avg_per_day,
        "peak_day": {"date": peak_day[0].isoformat(), "events": int(peak_day[1])} if peak_day else None,
        "peak_hour": {"hour": int(peak_hour_value[0]), "events": int(peak_hour_value[1])} if total_events else None,
        "first_event_at": first_event.isoformat() if first_event else None,
        "last_event_at": last_event.isoformat() if last_event else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/analytics/access")
def analytics_access(request: Request):
    """Small capability check used by the frontend to hide the owner console."""
    try:
        _authorized_email(request)
        return {"success": True, "allowed": True}
    except HTTPException as exc:
        if exc.status_code in {401, 403}:
            return {"success": True, "allowed": False}
        raise


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
