from __future__ import annotations

# ============================================================
# NOVA AI - API SERVER
# ============================================================

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
import asyncio
import time
import uuid
import traceback
import re
import secrets
import threading

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Query,
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import (
    StreamingResponse,
    JSONResponse,
)

from fastapi.exceptions import RequestValidationError

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)

from backend.core.nova_core import NovaCore

from backend.auth import (
    register_user,
    login_user,
)

from backend.settings import SettingsManager


# ============================================================
# APPLICATION METADATA
# ============================================================

APP_NAME = "Nova AI"
APP_VERSION = "1.0.0"

APP_DESCRIPTION = """
Nova AI educational assistant API.
"""


# ============================================================
# RUNTIME
# ============================================================

SERVER_STARTED_AT = time.time()

SERVER_STARTED_DATETIME = datetime.now(
    timezone.utc
).isoformat()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================
# CORS
# ============================================================

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    "http://localhost:5173",
    "http://127.0.0.1:5173",

    "http://localhost:5174",
    "http://127.0.0.1:5174",

    # Public Nova V1 frontend.
    "https://nova-frontend-i76e.onrender.com",
]

app.add_middleware(
    CORSMiddleware,

    allow_origins=ALLOWED_ORIGINS,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# NOVA CORE
# ============================================================
#
# IMPORTANT:
#
# NovaCore is intentionally NOT created during module import.
#
# If NovaCore crashes during initialization, FastAPI itself
# must still be able to start so that /health, /status and
# /frontend/ping can tell us what is actually broken.
#
# ============================================================

nova: Optional[NovaCore] = None

nova_init_error: Optional[str] = None


def get_nova() -> NovaCore:
    """
    Lazily initialize NovaCore.

    This prevents a NovaCore initialization error from killing
    the entire FastAPI application during import.
    """

    global nova
    global nova_init_error

    if nova is not None:
        return nova

    try:

        print()
        print("=" * 60)
        print("NOVA CORE INITIALIZATION")
        print("=" * 60)

        nova = NovaCore()

        nova_init_error = None

        print("Nova Core initialized successfully")
        print("=" * 60)

        return nova

    except Exception as error:

        nova_init_error = str(error)

        print()
        print("=" * 60)
        print("NOVA CORE INITIALIZATION FAILED")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60)

        raise RuntimeError(
            "Nova Core could not be initialized."
        ) from error
