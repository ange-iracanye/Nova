"""Fast production boot wrapper for Nova."""

from __future__ import annotations

import json
import os
import re
import traceback
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Awaitable, Callable

_REAL_APP: Any = None
_REAL_APP_ERROR: Exception | None = None

PUBLIC_FRONTEND_ORIGIN = "https://nova-frontend-i76e.onrender.com"
COOKIE_NAME = os.getenv("NOVA_SESSION_COOKIE", "nova_session")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _allowed_origins() -> set[str]:
    raw = os.getenv("NOVA_ALLOWED_ORIGINS", "")
    origins = {item.strip().rstrip("/") for item in raw.split(",") if item.strip()}
    origins.add(PUBLIC_FRONTEND_ORIGIN)
    return origins


def _request_origin(scope: dict[str, Any]) -> str:
    return next(
        (value.decode("latin-1") for name, value in scope.get("headers", []) if name.lower() == b"origin"),
        "",
    ).rstrip("/")


def _request_headers(scope: dict[str, Any]) -> dict[str, str]:
    return {
        name.decode("latin-1").lower(): value.decode("latin-1")
        for name, value in scope.get("headers", [])
    }


def _cors_headers(scope: dict[str, Any]) -> list[tuple[bytes, bytes]]:
    origin = _request_origin(scope)
    allowed = origin in _allowed_origins() or (
        origin.startswith("https://nova-frontend") and origin.endswith(".onrender.com")
    )
    if not allowed:
        return []
    return [
        (b"access-control-allow-origin", origin.encode("latin-1")),
        (b"access-control-allow-credentials", b"true"),
        (b"access-control-allow-methods", b"GET,POST,PUT,PATCH,DELETE,OPTIONS"),
        (b"access-control-allow-headers", b"Authorization,Content-Type,X-Nova-Session,X-Request-ID"),
        (b"vary", b"Origin"),
    ]


async def _send_json(
    send: Callable[..., Awaitable[None]],
    status: int,
    payload: dict[str, Any],
    headers_extra: list[tuple[bytes, bytes]] | None = None,
    cookies: list[str] | None = None,
) -> None:
    body = b"" if status in {204, 304} else json.dumps(payload).encode("utf-8")
    headers: list[tuple[bytes, bytes]] = [(b"cache-control", b"no-store")]
    if status not in {204, 304}:
        headers.insert(0, (b"content-type", b"application/json; charset=utf-8"))
        headers.append((b"content-length", str(len(body)).encode("ascii")))
    else:
        headers.append((b"content-length", b"0"))
    if headers_extra:
        headers.extend(headers_extra)
    for cookie in cookies or []:
        headers.append((b"set-cookie", cookie.encode("latin-1")))
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
    """Load the full application lazily without permanently caching failures."""
    global _REAL_APP, _REAL_APP_ERROR
    if _REAL_APP is not None:
        return _REAL_APP
    try:
        from backend.free_llm import FreeLLM
        import backend.tutor_system.tutor_engine as tutor_engine
        tutor_engine.LocalLLM = FreeLLM
        import backend.production as production
        _REAL_APP = production.app
        _REAL_APP_ERROR = None
        return _REAL_APP
    except Exception as exc:
        _REAL_APP_ERROR = exc
        print("Nova production application initialization failed:", flush=True)
        traceback.print_exc()
        raise

