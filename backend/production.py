"""Production application entrypoint for Nova.

Keeps backend.api's existing endpoint implementation intact while applying
production-only infrastructure at import time.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware

from backend import api
from backend import auth
from backend.persistent_sessions import PersistentSessionStore


# ---------------------------------------------------------------------------
# Persistent application data
# ---------------------------------------------------------------------------
# Render services have an ephemeral filesystem by default. The V1 Blueprint
# mounts /opt/render/project/src/data as a persistent disk, so all existing
# Nova JSON/embedding data written below ./data survives restarts and deploys.
DATA_DIR = Path(os.getenv("NOVA_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
auth.USERS_FILE = DATA_DIR / "users.json"


# ---------------------------------------------------------------------------
# Durable authentication sessions
# ---------------------------------------------------------------------------
# Replace the in-memory dict used by api.py with the compatible SQLite-backed
# mapping. Existing endpoints continue to use the same dict-style interface.
api.auth_sessions = PersistentSessionStore(
    os.getenv("NOVA_SESSION_DB", str(DATA_DIR / "sessions.sqlite3"))
)


# ---------------------------------------------------------------------------
# Deployment CORS
# ---------------------------------------------------------------------------
configured_origins = [
    origin.strip()
    for origin in os.getenv("NOVA_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

if configured_origins:
    api.app.add_middleware(
        CORSMiddleware,
        allow_origins=configured_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Nova-Session"],
    )


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
@api.app.middleware("http")
async def production_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if os.getenv("NOVA_ENV", "development").lower() == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


app = api.app
