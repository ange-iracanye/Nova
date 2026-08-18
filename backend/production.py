"""Production application entrypoint for Nova."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware

from backend import api
from backend import auth
from backend.persistent_sessions import PersistentSessionStore


# Render mounts the V1 data disk here. Keeping the application data directory
# in one place makes the existing JSON-based learning stores durable without
# forcing a risky storage rewrite immediately before V1.
DATA_DIR = Path(os.getenv("NOVA_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
auth.USERS_FILE = DATA_DIR / "users.json"


# Authentication sessions are durable and survive ordinary process restarts.
api.auth_sessions = PersistentSessionStore(
    os.getenv("NOVA_SESSION_DB", str(DATA_DIR / "sessions.sqlite3"))
)


# Deployment CORS. If the environment variable is supplied, it wins. The
# default covers the Blueprint's expected Render frontend hostname plus local
# development, so a first deployment can work before a custom domain exists.
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


@api.app.middleware("http")
async def production_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    if os.getenv("NOVA_ENV", "development").lower() == "production":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response


app = api.app
