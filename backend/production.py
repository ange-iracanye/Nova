"""Production application entrypoint for Nova."""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from backend import api
from backend import auth
from backend.persistent_sessions import PersistentSessionStore


DATA_DIR = Path(os.getenv("NOVA_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
auth.USERS_FILE = DATA_DIR / "users.json"
api.auth_sessions = PersistentSessionStore(os.getenv("NOVA_SESSION_DB", str(DATA_DIR / "sessions.sqlite3")))

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
    "/", "/api", "/health", "/ready", "/status", "/register", "/login",
    "/auth/session", "/auth/logout", "/docs", "/redoc", "/openapi.json", "/demo/session",
}
PUBLIC_PREFIXES = ("/demo/session/", "/demo/chat/")
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


def _cookie_session_token(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    session = api.auth_sessions.get(token)
    if not isinstance(session, dict):
        return None
    try:
        expires_at = datetime.fromisoformat(str(session.get("expires_at")))
    except (TypeError, ValueError):
        return None
    if expires_at <= datetime.now(timezone.utc):
        api.auth_sessions.pop(token, None)
        return None
    return token


def _inject_cookie_session(request: Request) -> str | None:
    token = _cookie_session_token(request)
    if not token:
        return None
    headers = list(request.scope.get("headers", []))
    if not any(name.lower() == b"x-nova-session" for name, _ in headers):
        headers.append((b"x-nova-session", token.encode("latin-1")))
        request.scope["headers"] = headers
    return token


async def _set_login_cookie(response: Response) -> Response:
    """Attach the server session as an HttpOnly cookie to auth responses."""
    if response.status_code not in {200, 201}:
        return response
    if not hasattr(response, "body_iterator"):
        return response
    body = b"".join([chunk async for chunk in response.body_iterator])
    try:
        payload = json.loads(body.decode("utf-8"))
        token = payload.get("session", {}).get("token")
    except (ValueError, AttributeError, UnicodeDecodeError):
        token = None
    if not isinstance(token, str) or not token:
        return Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    replacement = Response(content=body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    replacement.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    return replacement


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

    path = request.url.path
    is_public = path in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)
    if is_public:
        response = await call_next(request)
        if path in {"/login", "/register"}:
            response = await _set_login_cookie(response)
        if path == "/auth/logout":
            response.delete_cookie(COOKIE_NAME, path="/")
        return response

    cookie_token = _inject_cookie_session(request)
    if not cookie_token and not api.get_auth_session(request):
        return JSONResponse(status_code=401, content={"success": False, "error": {"code": "NOT_AUTHENTICATED", "message": "A valid Nova session is required."}})

    response = await call_next(request)
    token = cookie_token
    if not token:
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            token = request.headers.get("x-nova-session")
    if token and api.auth_sessions.get(token):
        response.set_cookie(key=COOKIE_NAME, value=token, max_age=7 * 24 * 60 * 60, httponly=True, secure=True, samesite=COOKIE_SAMESITE, path="/")
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
