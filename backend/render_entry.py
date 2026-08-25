"""Render entrypoint compatibility layer for Nova V1.

This wrapper keeps the existing production boot path intact while normalizing
responses for the deployed frontend and routing one legacy dashboard URL to
the production V1 dashboard implementation.
"""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from backend.boot import app as boot_app


async def _forward_with_rewrite(
    scope: dict[str, Any],
    receive: Callable[..., Awaitable[Any]],
    send: Callable[..., Awaitable[Any]],
) -> None:
    """Forward a request to boot.app, rewriting only the legacy dashboard path."""
    path = str(scope.get("path", ""))
    if path == "/dashboard":
        scope = dict(scope)
        scope["path"] = "/v1/dashboard"
        scope["raw_path"] = b"/v1/dashboard"

    await boot_app(scope, receive, send)


async def app(
    scope: dict[str, Any],
    receive: Callable[..., Awaitable[Any]],
    send: Callable[..., Awaitable[Any]],
) -> None:
    """Production ASGI application used by Render."""
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

    # The frontend's login compatibility layer accepts a top-level token.
    # The canonical backend response keeps the richer session object too.
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
