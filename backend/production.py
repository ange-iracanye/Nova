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
from backend.fast_runtime import install_fast_runtime
from backend.persistent_sessions import PersistentSessionStore

install_fast_runtime()

_ORIGINAL_STREAM_TEXT = api.stream_text


async def _fast_stream_text(text: str, chunk_size: int = 120, delay: float = 0.0):
    async for chunk in _ORIGINAL_STREAM_TEXT(text, chunk_size=chunk_size, delay=delay):
        yield chunk


api.stream_text = _fast_stream_text

DATA_DIR = Path(os.getenv("NOVA_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
auth.USERS_FILE = DATA_DIR / "users.json"
api.auth_sessions = PersistentSessionStore(
    os.getenv("NOVA_SESSION_DB", str(DATA_DIR / "sessions.sqlite3"))
)

ENVIRONMENT = os.getenv("NOVA_ENV", "development").strip().lower()
IS_PRODUCTION = ENVIRONMENT == "production"


def _configured_origins() -> list[str]:
    raw = os.getenv("NOVA_ALLOWED_ORIGINS", "")
    origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    if IS_PRODUCTION:
        # Production must never silently trust localhost or an example domain.
        if not origins:
            raise RuntimeError(
                "NOVA_ALLOWED_ORIGINS must be set to at least one HTTPS frontend origin in production."
            )
        insecure = [origin for origin in origins if not origin.startswith("https://")]
        if insecure:
            raise RuntimeError(
                "NOVA_ALLOWED_ORIGINS contains non-HTTPS origins in production: "
                + ", ".join(insecure)
            )
        return origins
    return origins or [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


configured_origins = _configured_origins()
api.app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Nova-Session"],
)

# API documentation is useful locally, but leaving interactive docs public on a
# production educational service is unnecessary attack surface. Operators can
# explicitly enable it with NOVA_ENABLE_DOCS=true when needed.
ENABLE_DOCS = os.getenv("NOVA_ENABLE_DOCS", "false" if IS_PRODUCTION else "true").lower() == "true"
ENABLE_DEMO = os.getenv("NOVA_ENABLE_DEMO", "false" if IS_PRODUCTION else "true").lower() == "true"

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
}
if ENABLE_DOCS:
    PUBLIC_PATHS.update({"/docs", "/redoc", "/openapi.json"})
if ENABLE_DEMO:
    PUBLIC_PATHS.add("/demo/session")

PUBLIC_PREFIXES: tuple[str, ...] = ("/demo/session/", "/demo/chat/") if ENABLE_DEMO else ()
COOKIE_NAME = os.getenv("NOVA_SESSION_COOKIE", "nova_session")
COOKIE_SAMESITE = os.getenv("NOVA_COOKIE_SAMESITE", "lax").lower()
if COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    COOKIE_SAMESITE = "lax"
if IS_PRODUCTION and COOKIE_SAMESITE == "none":
    # SameSite=None requires Secure and is only appropriate when the frontend
    # is intentionally cross-site. Keep Lax as the safe V1 default.
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
    # Render terminates TLS before forwarding to the service. Do not trust
    # arbitrary X-Forwarded-For values because they can be spoofed directly.
    return request.client.host if request.client else "unknown"


def _rate_limited(request: Request) -> bool:
    rule = _RATE_LIMITS.get(request.url.path)
    if not rule:
        return False
    limit, window = rule
    bucket = _rate_windows[(_client_key(request), request.url.path)]
    now = time.monotonic()
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
    if response.status_code not in {200, 201}:
        return response
    body = getattr(response, "body", None)
    if not isinstance(body, (bytes, bytearray)):
        return response
    try:
        payload = json.loads(bytes(body).decode("utf-8"))
        token = payload.get("session", {}).get("token")
    except (ValueError, AttributeError, UnicodeDecodeError):
        token = None
    replacement = Response(
        content=bytes(body),
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )
    if isinstance(token, str) and token:
        replacement.set_cookie(
            key=COOKIE_NAME,
            value=token,
            max_age=7 * 24 * 60 * 60,
            httponly=True,
            secure=IS_PRODUCTION,
            samesite=COOKIE_SAMESITE,
            path="/",
        )
    return replacement


@api.app.middleware("http")
async def production_auth_boundary(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    if not IS_PRODUCTION:
        return await call_next(request)

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": {"code": "INVALID_CONTENT_LENGTH", "message": "Invalid request size."}},
            )
        limit = MAX_UPLOAD_BYTES if request.url.path.startswith("/upload") else MAX_BODY_BYTES
        if size > limit:
            return JSONResponse(
                status_code=413,
                content={"success": False, "error": {"code": "REQUEST_TOO_LARGE", "message": "Request is too large."}},
            )

    if _rate_limited(request):
        return JSONResponse(
            status_code=429,
            content={"success": False, "error": {"code": "RATE_LIMITED", "message": "Too many requests. Please try again shortly."}},
        )

    path = request.url.path
    if path in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
        response = await call_next(request)
        if path in {"/login", "/register"}:
            response = await _set_login_cookie(response)
        if path == "/auth/logout":
            response.delete_cookie(COOKIE_NAME, path="/")
        return response

    cookie_token = _inject_cookie_session(request)
    if not cookie_token and not api.get_auth_session(request):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": {"code": "NOT_AUTHENTICATED", "message": "A valid Nova session is required."}},
        )

    response = await call_next(request)
    token = cookie_token
    if not token:
        authorization = request.headers.get("authorization", "")
        token = authorization[7:].strip() if authorization.lower().startswith("bearer ") else request.headers.get("x-nova-session")
    if token and api.auth_sessions.get(token):
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
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
    if request.url.path.startswith("/auth/"):
        response.headers.setdefault("Cache-Control", "no-store")
    if IS_PRODUCTION:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


app = api.app
