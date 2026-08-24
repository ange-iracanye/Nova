"""Fast production boot wrapper for Nova.

Render health checks must be able to reach a listening HTTP process before
Nova's optional ML/runtime dependency tree is imported. This wrapper keeps
startup lightweight and loads the full production application on the first
non-health request.
"""

from __future__ import annotations

import json
import os
from typing import Any, Awaitable, Callable


_REAL_APP: Any = None
_REAL_APP_ERROR: Exception | None = None


async def _send_json(send: Callable[..., Awaitable[None]], status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"cache-control", b"no-store"),
        ],
    })
    await send({
        "type": "http.response.body",
        "body": body,
    })


def _load_real_app() -> Any:
    global _REAL_APP, _REAL_APP_ERROR

    if _REAL_APP is not None:
        return _REAL_APP
    if _REAL_APP_ERROR is not None:
        raise _REAL_APP_ERROR

    try:
        # Patch the legacy TutorEngine default before the production app is
        # constructed so the public V1 path uses OpenRouter rather than Ollama.
        from backend.free_llm import FreeLLM
        import backend.tutor_system.tutor_engine as tutor_engine

        tutor_engine.LocalLLM = FreeLLM

        import backend.production as production

        _REAL_APP = production.app
        return _REAL_APP
    except Exception as exc:
        _REAL_APP_ERROR = exc
        raise


def _database_probe() -> tuple[bool, str | None]:
    """Perform a lightweight PostgreSQL authentication/connectivity probe.

    This intentionally checks only connectivity and authentication. It never
    returns the connection string or database error details to the client.
    """
    url = os.getenv("NOVA_DATABASE_URL", "").strip()
    if not url:
        return False, "NOVA_DATABASE_URL is not configured"

    try:
        import psycopg

        with psycopg.connect(url, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return True, None
    except Exception:
        return False, "PostgreSQL connectivity/authentication failed"


def _openrouter_probe() -> tuple[bool, str | None]:
    if not os.getenv("OPENROUTER_API_KEY", "").strip():
        return False, "OPENROUTER_API_KEY is not configured"
    return True, None


async def app(scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[None]]) -> None:
    if scope.get("type") != "http":
        real_app = _load_real_app()
        await real_app(scope, receive, send)
        return

    path = scope.get("path", "/")

    if path == "/health":
        await _send_json(send, 200, {
            "success": True,
            "status": "healthy",
            "service": "nova-api",
            "version": "1.0.0",
        })
        return

    if path == "/ready":
        required = ("NOVA_ENV", "NOVA_ALLOWED_ORIGINS")
        missing = [key for key in required if not os.getenv(key, "").strip()]
        if missing:
            await _send_json(send, 503, {
                "success": False,
                "status": "not_ready",
                "missing": missing,
            })
            return

        db_ok, db_error = _database_probe()
        llm_ok, llm_error = _openrouter_probe()
        if not db_ok or not llm_ok:
            checks: dict[str, str] = {}
            if not db_ok:
                checks["database"] = db_error or "unavailable"
            if not llm_ok:
                checks["openrouter"] = llm_error or "unavailable"
            await _send_json(send, 503, {
                "success": False,
                "status": "not_ready",
                "checks": checks,
            })
            return

        await _send_json(send, 200, {
            "success": True,
            "status": "ready",
            "service": "nova-api",
            "runtime": "lazy",
            "checks": {
                "database": "ok",
                "openrouter": "configured",
            },
        })
        return

    try:
        real_app = _load_real_app()
    except Exception:
        await _send_json(send, 503, {
            "success": False,
            "error": {
                "code": "PRODUCTION_APP_INIT_FAILED",
                "message": "Nova is temporarily unavailable while the application runtime starts.",
            },
        })
        return

    await real_app(scope, receive, send)
