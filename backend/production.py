"""Production application entrypoint for Nova.

This module keeps the existing API implementation intact while adding the
small amount of infrastructure that should only exist in a public deployment:
persistent sessions, durable application data, deployment CORS, security
headers, authentication boundaries, request limits, and cookie-backed
sessions.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from http.cookies import SimpleCookie
from pathlib import Path

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import api
from backend import auth
from backend.persistent_sessions import PersistentSessionStore


DATA_DIR = Path(os.getenv("NOVA_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
auth.USERS_FILE = DATA_DIR / "users.json"

api.auth_sessions = PersistentSessionStore(
    os.getenv("NOVA_SESSION_DB", str(DATA_DIR / "sessions.sqlite3"))
)

configured_origins = [
    origin.strip()
    for origin in os.getenv(
        "NOVA_ALLOWED_ORIGINS",
        "https://nova-frontend.onrender.com,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

api.app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Nova-Session"],
)


PUBLIC_PATHS = {
    "/",
    "/api",
    "/health",
    "/ready",
    "/status",
    "/register",
    "/login",
    "/auth/session",
    "/auth/logout",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/demo/session",
}

PUBLIC_PREFIXES = (
    "/demo/session/",
    "/demo/chat/",
)

COOKIE_NAME = os.getenv("NOVA_SESSION_COOKIE", "nova_session")
COOKIE_SAMESITE = os.getenv("NOVA_COOKIE_SAMESITE", "lax").lower()
if COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    COOKIE_SAMESITE = "lax"

MAX_BODY_BYTES = int(os.getenv("NOVA_MAX_BODY_BYTES", str(512 * 1024)))
MAX_UPLOAD_BYTES = int(os.getenv("NOVA_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

_RATE_LIMITS = {
    "/login": (10, 300),
    "/register": (8, 600),
    "/chat": (30, 60),
    "/chat/stream": (30, 60),
    "/demo/chat/stream": (20, 60),
}
_rate_windows: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limited(request: Request) -> bool:
    rule = _RATE_LIMITS.get(request.url.path)
    if not rule:
        return False
    limit, window = rule
    key = (_client_key(request), request.url.path)
    now = time.monotonic()
    bucket = _rate_windows[key]
    while bucket and now - bucket[0] >= window:
        bucket.popleft()
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def _inject_cookie_session(request: Request) -> str | None:
    """Make the HttpOnly cookie usable by the legacy API session resolver."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    if not api.get_auth_session(request):
        return None
    # Starlette exposes request headers through the ASGI scope. Injecting the
    # already-validated cookie token lets the existing API remain compatible
    # without duplicating the session store in this deployment wrapper.
    headers = list(request.scope.get("headers", []))
    lower_names = {name.lower() for name, _ in headers}
    if b"x-nova-session" not in lower_names:
        headers.append((b"x-nova-session", token.encode("latin-1")))
        request.scope["headers"] = headers
    return token


@api.app.middleware("http")
async def production_auth_boundary(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    if os.getenv("NOVA_ENV", "development").lower() != "production":
        return await call_next(request)

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
        except ValueError:
            return JSONResponse(status_code=400, content={"success": False, "error": {"code": "INVALID_CONTENT_LENGTH", "message": "Invalid request size."}})
        limit = MAX_UPLOAD_BYTES if request.url.path.startswith("/upload") else MAX_BODY_BYTES
        if size > limit:
            return JSONResponse(status_code=413, content={"success": False, "error": {"code": "REQUEST_TOO_LARGE", "message": "Request is too large."}})

    if _rate_limited(request):
        return JSONResponse(status_code=429, content={"success": False, "error": {"code": "RATE_LIMITED", "message": "Too many requests. Please try again shortly."}})

    if request.url.path in PUBLIC_PATHS or any(request.url.path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
        return await call_next(request)

    cookie_token = _inject_cookie_session(request)
    if not cookie_token and not api.get_auth_session(request):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {
                    "code": "NOT_AUTHENTICATED",
                    "message": "A valid Nova session is required.",
                },
            },
        )

    response = await call_next(request)

    # Upgrade an existing bearer/header session into a browser cookie. The
    # cookie is HttpOnly so frontend JavaScript cannot read it after this point.
    token = cookie_token
    if not token:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            token = request.headers.get("x-nova-session")
    if token and api.get_auth_session(request):
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            max_age=7 * 24 * 60 * 60,
            httponly=True,
            secure=True,
            samesite=COOKIE_SAMESITE,
            path="/",
        )
    return response


@api.app.middleware("http")
async def production_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

    if request.url.path.startswith("/auth/"):
        response.headers.setdefault("Cache-Control", "no-store")

    if os.getenv("NOVA_ENV", "development").lower() == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    return response


app = api.app
