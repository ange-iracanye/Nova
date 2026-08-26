"""Render entrypoint compatibility layer for Nova V1."""

from __future__ import annotations

import json
import os
from typing import Any, Awaitable, Callable

from backend.boot import app as boot_app

PUBLIC_FRONTEND_ORIGIN = "https://nova-frontend-i76e.onrender.com"


def _allowed_origins() -> set[str]:
    raw = os.getenv("NOVA_ALLOWED_ORIGINS", "")
    origins = {item.strip().rstrip("/") for item in raw.split(",") if item.strip()}
    origins.add(PUBLIC_FRONTEND_ORIGIN)
    return origins


def _origin(scope: dict[str, Any]) -> str:
    return next(
        (
            value.decode("latin-1")
            for name, value in scope.get("headers", [])
            if name.lower() == b"origin"
        ),
        "",
    ).rstrip("/")


def _origin_is_allowed(origin: str) -> bool:
    if not origin:
        return False
    if origin in _allowed_origins():
        return True
    return origin.startswith("https://")


def _cors_headers(scope: dict[str, Any]) -> list[tuple[bytes, bytes]]:
    origin = _origin(scope)
    if not _origin_is_allowed(origin):
        return []
    return [
        (b"access-control-allow-origin", origin.encode("latin-1")),
        (b"access-control-allow-credentials", b"true"),
        (b"access-control-allow-methods", b"GET,POST,PUT,PATCH,DELETE,OPTIONS"),
        (b"access-control-allow-headers", b"Authorization,Content-Type,X-Nova-Session,X-Request-ID"),
        (b"access-control-max-age", b"600"),
        (b"vary", b"Origin"),
    ]


def _with_cors(headers: list[tuple[bytes, bytes]], cors: list[tuple[bytes, bytes]]) -> list[tuple[bytes, bytes]]:
    """Replace conflicting CORS headers instead of leaving two origins behind."""
    if not cors:
        return headers
    cors_names = {name.lower() for name, _ in cors}
    filtered = [(name, value) for name, value in headers if name.lower() not in cors_names]
    filtered.extend(cors)
    return filtered


async def _send_fast_json(send: Callable[..., Awaitable[Any]], status: int, payload: dict[str, Any], scope: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = [
        (b"content-type", b"application/json; charset=utf-8"),
        (b"content-length", str(len(body)).encode("ascii")),
        (b"cache-control", b"no-store"),
    ]
    headers.extend(_cors_headers(scope))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


async def _send_options(send: Callable[..., Awaitable[Any]], scope: dict[str, Any]) -> None:
    headers = [(b"content-length", b"0"), (b"cache-control", b"no-store")]
    headers.extend(_cors_headers(scope))
    await send({"type": "http.response.start", "status": 204, "headers": headers})
    await send({"type": "http.response.body", "body": b""})


async def _forward_with_rewrite(scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:
    """Forward requests to boot.app while forcing one correct CORS origin."""
    path = str(scope.get("path", ""))
    if path == "/dashboard":
        scope = dict(scope)
        scope["path"] = "/v1/dashboard"
        scope["raw_path"] = b"/v1/dashboard"

    cors = _cors_headers(scope)

    async def cors_send(message: dict[str, Any]) -> None:
        if message.get("type") == "http.response.start" and cors:
            headers = _with_cors(list(message.get("headers", [])), cors)
            message = {**message, "headers": headers}
        await send(message)

    await boot_app(scope, receive, cors_send)


async def app(scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:
    """Production ASGI application used by Render."""
    if scope.get("type") != "http":
        await _forward_with_rewrite(scope, receive, send)
        return

    path = str(scope.get("path", ""))

    if scope.get("method") == "OPTIONS":
        await _send_options(send, scope)
        return

    if path == "/":
        await _send_fast_json(send, 200, {"success": True, "service": "nova-api", "status": "healthy"}, scope)
        return

    if path in {"/health", "/ready"}:
        await _send_fast_json(send, 200, {"success": True, "status": "healthy", "service": "nova-api"}, scope)
        return

    if path not in {"/login", "/register"}:
        await _forward_with_rewrite(scope, receive, send)
        return

    messages: list[dict[str, Any]] = []

    async def capture(message: dict[str, Any]) -> None:
        messages.append(message)

    await _forward_with_rewrite(scope, receive, capture)

    response_body = bytearray()
    for message in messages:
        if message.get("type") == "http.response.body":
            response_body.extend(message.get("body", b""))

    try:
        payload = json.loads(bytes(response_body).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = None

    if isinstance(payload, dict) and isinstance(payload.get("session"), dict):
        token = payload["session"].get("token")
        if isinstance(token, str) and token:
            payload.setdefault("token", token)
            payload.setdefault("token_type", "Bearer")
            new_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            for message in messages:
                if message.get("type") == "http.response.start":
                    message["headers"] = [
                        (name, str(len(new_body)).encode("ascii") if name.lower() == b"content-length" else value)
                        for name, value in message.get("headers", [])
                    ]
                    break
            for message in messages:
                if message.get("type") == "http.response.body":
                    message["body"] = new_body
                    message["more_body"] = False
                    break

    cors = _cors_headers(scope)
    for message in messages:
        if message.get("type") == "http.response.start" and cors:
            message["headers"] = _with_cors(list(message.get("headers", [])), cors)
        await send(message)
