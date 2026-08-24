"""Fast production boot wrapper for Nova."""

from __future__ import annotations

import json
import os
import traceback
from typing import Any, Awaitable, Callable

_REAL_APP: Any = None
_REAL_APP_ERROR: Exception | None = None

PUBLIC_FRONTEND_ORIGIN = "https://nova-frontend-i76e.onrender.com"


def _request_origin(scope: dict[str, Any]) -> str:
    return next(
        (value.decode("latin-1") for name, value in scope.get("headers", []) if name.lower() == b"origin"),
        "",
    )


def _cors_headers(scope: dict[str, Any]) -> list[tuple[bytes, bytes]]:
    """Return CORS response headers for the public frontend.

    Production health/readiness responses are served directly by this ASGI
    wrapper, before FastAPI's CORSMiddleware exists in the request chain.
    The wrapper therefore has to add CORS headers itself for those responses,
    and for startup-error responses as well.
    """
    origin = _request_origin(scope)
    if origin != PUBLIC_FRONTEND_ORIGIN:
        return []
    return [
        (b"access-control-allow-origin", origin.encode("latin-1")),
        (b"access-control-allow-credentials", b"true"),
        (b"vary", b"Origin"),
    ]


async def _send_json(
    send: Callable[..., Awaitable[None]],
    status: int,
    payload: dict[str, Any],
    headers_extra: list[tuple[bytes, bytes]] | None = None,
) -> None:
    body = json.dumps(payload).encode("utf-8")
    headers = [
        (b"content-type", b"application/json; charset=utf-8"),
        (b"cache-control", b"no-store"),
    ]
    if headers_extra:
        headers.extend(headers_extra)
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


async def _handle_lifespan(receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:
    while True:
        message = await receive()
        message_type = message.get("type")
        if message_type == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message_type == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return


def _load_real_app() -> Any:
    global _REAL_APP, _REAL_APP_ERROR
    if _REAL_APP is not None:
        return _REAL_APP
    if _REAL_APP_ERROR is not None:
        raise _REAL_APP_ERROR
    try:
        from backend.free_llm import FreeLLM
        import backend.tutor_system.tutor_engine as tutor_engine
        tutor_engine.LocalLLM = FreeLLM
        import backend.production as production
        _REAL_APP = production.app
        return _REAL_APP
    except Exception as exc:
        _REAL_APP_ERROR = exc
        print("Nova production application initialization failed:", flush=True)
        traceback.print_exc()
        raise


def _database_probe() -> tuple[bool, str | None]:
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


async def _handle_preflight(scope: dict[str, Any], send: Callable[..., Awaitable[Any]]) -> None:
    origin = _request_origin(scope)
    allowed = origin == PUBLIC_FRONTEND_ORIGIN
    headers: list[tuple[bytes, bytes]] = [
        (b"access-control-allow-methods", b"GET, POST, PUT, PATCH, DELETE, OPTIONS"),
        (b"access-control-allow-headers", b"Authorization, Content-Type, X-Nova-Session, X-Request-ID"),
        (b"access-control-allow-credentials", b"true"),
        (b"access-control-max-age", b"600"),
        (b"vary", b"Origin"),
    ]
    if allowed:
        headers.append((b"access-control-allow-origin", origin.encode("latin-1")))
        await _send_json(send, 204, {}, headers)
    else:
        await _send_json(
            send,
            403,
            {"success": False, "error": {"code": "CORS_ORIGIN_DENIED", "message": "Origin is not allowed."}},
            headers,
        )


async def _send_to_real_app_with_cors(
    scope: dict[str, Any],
    receive: Callable[..., Awaitable[Any]],
    send: Callable[..., Awaitable[Any]],
    real_app: Any,
) -> None:
    """Proxy ASGI response events and guarantee CORS on production responses."""
    cors = _cors_headers(scope)

    async def cors_send(message: dict[str, Any]) -> None:
        if message.get("type") == "http.response.start" and cors:
            headers = list(message.get("headers", []))
            existing = {name.lower() for name, _ in headers}
            for name, value in cors:
                if name.lower() not in existing:
                    headers.append((name, value))
            message = {**message, "headers": headers}
        await send(message)

    await real_app(scope, receive, cors_send)


async def app(
    scope: dict[str, Any],
    receive: Callable[..., Awaitable[Any]],
    send: Callable[..., Awaitable[Any]],
) -> None:
    scope_type = scope.get("type")

    if scope_type == "lifespan":
        await _handle_lifespan(receive, send)
        return

    if scope_type != "http":
        real_app = _load_real_app()
        await real_app(scope, receive, send)
        return

    path = scope.get("path", "/")
    method = scope.get("method", "GET").upper()

    # Render/browser CORS preflight must never require the heavy Nova runtime.
    if method == "OPTIONS":
        await _handle_preflight(scope, send)
        return

    # These endpoints intentionally stay lightweight. They also need CORS
    # because they bypass FastAPI's middleware by design.
    if path == "/health":
        await _send_json(
            send,
            200,
            {"success": True, "status": "healthy", "service": "nova-api", "version": "1.0.0"},
            _cors_headers(scope),
        )
        return

    if path == "/ready":
        required = ("NOVA_ENV", "NOVA_ALLOWED_ORIGINS")
        missing = [key for key in required if not os.getenv(key, "").strip()]
        if missing:
            await _send_json(
                send,
                503,
                {"success": False, "status": "not_ready", "missing": missing},
                _cors_headers(scope),
            )
            return
        db_ok, db_error = _database_probe()
        llm_ok, llm_error = _openrouter_probe()
        if not db_ok or not llm_ok:
            checks: dict[str, str] = {}
            if not db_ok:
                checks["database"] = db_error or "unavailable"
            if not llm_ok:
                checks["openrouter"] = llm_error or "unavailable"
            await _send_json(
                send,
                503,
                {"success": False, "status": "not_ready", "checks": checks},
                _cors_headers(scope),
            )
            return
        await _send_json(
            send,
            200,
            {"success": True, "status": "ready", "service": "nova-api", "runtime": "lazy", "checks": {"database": "ok", "openrouter": "configured"}},
            _cors_headers(scope),
        )
        return

    try:
        real_app = _load_real_app()
    except Exception:
        await _send_json(
            send,
            503,
            {"success": False, "error": {"code": "PRODUCTION_APP_INIT_FAILED", "message": "Nova is temporarily unavailable while the application runtime starts."}},
            _cors_headers(scope),
        )
        return

    await _send_to_real_app_with_cors(scope, receive, send, real_app)
