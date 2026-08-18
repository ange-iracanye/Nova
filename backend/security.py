from __future__ import annotations

import os
import secrets
import time
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import Response


SESSION_COOKIE_NAME = "nova_session"
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60

TRUSTED_DEV_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}


def is_production() -> bool:
    return os.getenv("NOVA_ENV", "development").strip().lower() == "production"


def allowed_origins() -> list[str]:
    configured = os.getenv("NOVA_ALLOWED_ORIGINS", "")
    origins = [item.strip().rstrip("/") for item in configured.split(",") if item.strip()]
    if origins:
        return origins
    if is_production():
        return []
    return sorted(TRUSTED_DEV_ORIGINS)


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=is_production(),
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=is_production(),
        samesite="lax",
        path="/",
    )


def get_cookie_session_token(request: Request) -> Optional[str]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    token = token.strip()
    return token or None


def get_client_ip(request: Request) -> str:
    client = request.client
    return client.host if client else "unknown"


def request_id() -> str:
    return secrets.token_hex(16)


def apply_security_headers(response: Response) -> Response:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
    if is_production():
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response


def authenticate_session(request: Request, sessions: dict, lock) -> dict:
    token = get_cookie_session_token(request)
    if not token:
        authorization = request.headers.get("Authorization", "").strip()
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip() or None

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    now = time.time()
    with lock:
        session = sessions.get(token)
        if not isinstance(session, dict):
            raise HTTPException(status_code=401, detail="Invalid or expired session.")

        expires_at = session.get("expires_at")
        if not expires_at:
            sessions.pop(token, None)
            raise HTTPException(status_code=401, detail="Invalid or expired session.")

        session["last_seen_epoch"] = now
        return dict(session)


def require_same_user(
    request: Request,
    sessions: dict,
    lock,
    supplied_email: Optional[str] = None,
) -> str:
    session = authenticate_session(request, sessions, lock)
    email = str(session.get("email", "")).strip().lower()

    if not email:
        raise HTTPException(status_code=401, detail="Invalid authenticated session.")

    if supplied_email and supplied_email.strip().lower() != email:
        raise HTTPException(
            status_code=403,
            detail="The supplied account does not match the authenticated session.",
        )

    return email
