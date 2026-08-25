"""Render entrypoint compatibility layer for Nova V1.

The Render entrypoint keeps the public boot path lightweight during platform
port detection and forwards application traffic to the production ASGI app.
"""

from __future__ import annotations

import json
import os
from typing import Any, Awaitable, Callable

from backend.boot import app as boot_app


def _allowed_origins() -> set[str]:
    raw = os.getenv("NOVA_ALLOWED_ORIGINS", "")
    return {item.strip().rstrip("/") for item in raw.split(",") if item.strip()}


def _origin(scope: dict[str, Any]) -> str:
    return next(
        (value.decode("latin-1") for name, value in scope.get("headers", []) if name.lower() == b"origin"),
        "",
    )


def _cors_headers(scope: dict[str, Any]) -> list[tuple[bytes, bytes]]:
    origin = _origin(scope)
    if not origin or origin not in _allowed_origins():
        return []
    return [
        (b"access-control-allow-origin", origin.encode("latin-1")),
        (b"access-control-allow-credentials", b"true"),
        (b"vary", b"Origin"),
    ]


async def _send_fast_json(
    send: Callable[..., Awaitable[Any]],
    status: int,
    payload: dict[str, Any],
    scope: dict[str, Any],
) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = [
        (b"content-type", b"application/json; charset=utf-8"),
        (b"content-length", str(len(body)).encode("ascii")),
        (b"cache-control", b"no-store"),
    ]
    headers.extend(_cors_headers(scope))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


async def _forward_with_rewrite(
    scope: dict[str, Any],
    receive: Callable[..., Awaitable[Any]],
    send: Callable[..., Awaitable[Any]],
) -> None:
    """Forward requests to boot.app while preserving production CORS headers."""
    path = str(scope.get("path", ""))
    if path == "/dashboard":
        scope = dict(scope)
        scope["path"] = "/v1/dashboard"
        scope["raw_path"] = b"/v1/dashboard"

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

    await boot_app(scope, receive, cors_send)


async def app(
    scope: dict[str, Any],
    receive: Callable[..., Awaitable[Any]],
    send: Callable[..., Awaitable[Any]],
) -> None:
    """Production ASGI application used by Render."""
    if scope.get("type") == "http" and scope.get("path") == "/":
        await _send_fast_json(
            send,
            200,
            {"success": True, "service": "nova-api", "status": "healthy"},
            scope,
        )
        return

    if scope.get("type") != "http" or scope.get("path") not in {"/login", "/register"}:
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
                    headers = []
                    for name, value in message.get("headers", []):
                        if name.lower() == b"content-length":
                            headers.append((name, str(len(new_body)).encode("ascii")))
                        else:
                            headers.append((name, value))
                    message["headers"] = headers
                    break
            for message in messages:
                if message.get("type") == "http.response.body":
                    message["body"] = new_body
                    message["more_body"] = False
                    break

    for message in messages:
        await send(message)
