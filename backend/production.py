"""Production application entrypoint for Nova.

This module keeps the existing API implementation intact while adding the
small amount of infrastructure that should only exist in a public deployment:
persistent sessions, durable application data, deployment CORS, security
headers, and production authentication boundaries.
"""

from __future__ import annotations

import os
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


# In development the legacy email-based compatibility path remains available.
# In production every account/data endpoint requires a real authenticated
# session, preventing a caller from impersonating another user by changing an
# email field in a request body.
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


@api.app.middleware("http")
async def production_auth_boundary(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    if os.getenv("NOVA_ENV", "development").lower() != "production":
        return await call_next(request)

    path = request.url.path
    is_public = path in PUBLIC_PATHS or any(
        path.startswith(prefix) for prefix in PUBLIC_PREFIXES
    )

    if not is_public and not api.get_auth_session(request):
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

    return await call_next(request)


@api.app.middleware("http")
async def production_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )

    if request.url.path.startswith("/auth/"):
        response.headers.setdefault("Cache-Control", "no-store")

    if os.getenv("NOVA_ENV", "development").lower() == "production":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

    return response


app = api.app
