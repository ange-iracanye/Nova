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
        # The production module currently imports the legacy TutorEngine
        # during its application construction. Before the first real Nova
        # request, replace that engine's Ollama adapter with the V1-only
        # OpenRouter free adapter. This keeps the public deployment on the
        # provider selected for V1 without changing local/dev compatibility.
        from backend.free_llm import FreeLLM
        import backend.production as production
        import backend.tutor_system.tutor_engine as tutor_engine

        tutor_engine.LocalLLM = FreeLLM
        _REAL_APP = production.app
        return _REAL_APP
    except Exception as exc:
        _REAL_APP_ERROR = exc
        raise


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
        # Readiness means the web process is alive and production-critical
        # environment configuration is present. NovaCore remains lazy so a
        # slow ML import cannot make Render declare the service dead.
        required = ("NOVA_ENV", "NOVA_ALLOWED_ORIGINS")
        missing = [key for key in required if not os.getenv(key, "").strip()]
        if missing:
            await _send_json(send, 503, {
                "success": False,
                "status": "not_ready",
                "missing": missing,
            })
            return
        await _send_json(send, 200, {
            "success": True,
            "status": "ready",
            "service": "nova-api",
            "runtime": "lazy",
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
