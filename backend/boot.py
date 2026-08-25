"""Fast production boot wrapper for Nova."""

from __future__ import annotations

import json
import os
import re
import traceback
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Awaitable, Callable

_REAL_APP: Any = None
_REAL_APP_ERROR: Exception | None = None

PUBLIC_FRONTEND_ORIGIN = "https://nova-frontend-i76e.onrender.com"
COOKIE_NAME = os.getenv("NOVA_SESSION_COOKIE", "nova_session")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _allowed_origins() -> set[str]:
    raw = os.getenv("NOVA_ALLOWED_ORIGINS", "")
    origins = {item.strip().rstrip("/") for item in raw.split(",") if item.strip()}
    origins.add(PUBLIC_FRONTEND_ORIGIN)
    return origins


def _origin_allowed(origin: str) -> bool:
    origin = origin.rstrip("/")
    return origin in _allowed_origins() or (
        origin.startswith("https://nova-frontend") and origin.endswith(".onrender.com")
    )


def _request_origin(scope: dict[str, Any]) -> str:
    return next(
        (value.decode("latin-1") for name, value in scope.get("headers", []) if name.lower() == b"origin"),
        "",
    ).rstrip("/")


def _request_headers(scope: dict[str, Any]) -> dict[str, str]:
    return {
        name.decode("latin-1").lower(): value.decode("latin-1")
        for name, value in scope.get("headers", [])
    }


def _cors_headers(scope: dict[str, Any]) -> list[tuple[bytes, bytes]]:
    origin = _request_origin(scope)
    if not origin or not _origin_allowed(origin):
        return []
    return [
        (b"access-control-allow-origin", origin.encode("latin-1")),
        (b"access-control-allow-credentials", b"true"),
        (b"access-control-allow-methods", b"GET, POST, PUT, PATCH, DELETE, OPTIONS"),
        (b"access-control-allow-headers", b"Authorization, Content-Type, X-Nova-Session, X-Request-ID"),
        (b"vary", b"Origin"),
    ]


async def _send_json(
    send: Callable[..., Awaitable[None]],
    status: int,
    payload: dict[str, Any],
    headers_extra: list[tuple[bytes, bytes]] | None = None,
    cookies: list[str] | None = None,
) -> None:
    body = b"" if status in {204, 304} else json.dumps(payload).encode("utf-8")
    headers: list[tuple[bytes, bytes]] = [(b"cache-control", b"no-store")]
    if status not in {204, 304}:
        headers.insert(0, (b"content-type", b"application/json; charset=utf-8"))
        headers.append((b"content-length", str(len(body)).encode("ascii")))
    else:
        headers.append((b"content-length", b"0"))
    if headers_extra:
        headers.extend(headers_extra)
    for cookie in cookies or []:
        headers.append((b"set-cookie", cookie.encode("latin-1")))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


async def _handle_lifespan(receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:
    while True:
        message = await receive()
        message_type = message.get("type")
        if message_type == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message_type == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return


def _load_real_app() -> Any:
    """Load the full application lazily without permanently caching failures."""
    global _REAL_APP, _REAL_APP_ERROR
    if _REAL_APP is not None:
        return _REAL_APP
    try:
        from backend.free_llm import FreeLLM
        import backend.tutor_system.tutor_engine as tutor_engine
        tutor_engine.LocalLLM = FreeLLM
        import backend.production as production
        _REAL_APP = production.app
        _REAL_APP_ERROR = None
        return _REAL_APP
    except Exception as exc:
        _REAL_APP_ERROR = exc
        print("Nova production application initialization failed:", flush=True)
        traceback.print_exc()
        raise


def _database_probe() -> tuple[bool, str | None]:
    url = os.getenv("NOVA_DATABASE_URL", "").strip()
    if not url:
        return False, "NOVA_DATABASE_URL is not configured"
    try:
        import psycopg
        with psycopg.connect(url, connect_timeout=5, sslmode="require") as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return True, None
    except Exception:
        return False, "PostgreSQL connectivity/authentication failed"


def _openrouter_probe() -> tuple[bool, str | None]:
    if not os.getenv("OPENROUTER_API_KEY", "").strip():
        return False, "OPENROUTER_API_KEY is not configured"
    return True, None


def _get_auth_components():
    from backend import auth
    from backend.persistent_sessions import PersistentSessionStore
    store = PersistentSessionStore(os.getenv("NOVA_SESSION_DB", "data/sessions.sqlite3"))
    return auth, store


def _new_session(email: str, store: Any) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    session = {
        "token": uuid.uuid4().hex + uuid.uuid4().hex,
        "email": email,
        "created_at": now.isoformat(),
        "last_seen": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
    }
    store[session["token"]] = session
    return session


def _cookie_header(token: str) -> str:
    secure = "; Secure" if os.getenv("NOVA_ENV", "development").strip().lower() == "production" else ""
    return f"{COOKIE_NAME}={token}; Max-Age=604800; Path=/; HttpOnly; SameSite=Lax{secure}"


def _clear_cookie_header() -> str:
    secure = "; Secure" if os.getenv("NOVA_ENV", "development").strip().lower() == "production" else ""
    return f"{COOKIE_NAME}=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax{secure}"


def _cookie_token(headers: dict[str, str]) -> str | None:
    raw = headers.get("cookie", "")
    for item in raw.split(";"):
        key, _, value = item.strip().partition("=")
        if key == COOKIE_NAME and value:
            return value
    return None


def _session_from_request(headers: dict[str, str], store: Any) -> dict[str, Any] | None:
    token = headers.get("x-nova-session")
    if not token:
        authorization = headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
    if not token:
        token = _cookie_token(headers)
    if not token:
        return None
    session = store.get(token)
    if not isinstance(session, dict):
        return None
    try:
        expires_at = datetime.fromisoformat(str(session.get("expires_at")))
    except (TypeError, ValueError):
        store.pop(token, None)
        return None
    if expires_at <= datetime.now(timezone.utc):
        store.pop(token, None)
        return None
    return session


async def _handle_auth_fallback(scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> bool:
    path = scope.get("path", "/")
    method = scope.get("method", "GET").upper()
    if path not in {"/register", "/login", "/auth/session", "/auth/me", "/auth/logout"}:
        return False
    try:
        auth, store = _get_auth_components()
        headers = _request_headers(scope)
        cors = _cors_headers(scope)
        if method == "GET" and path in {"/auth/session", "/auth/me"}:
            session = _session_from_request(headers, store)
            if not session:
                await _send_json(send, 401 if path == "/auth/me" else 200, {"success": path == "/auth/session", "authenticated": False, "user": None, "session": None}, cors)
                return True
            await _send_json(send, 200, {"success": True, "authenticated": True, "user": {"email": session["email"]}, "session": session}, cors)
            return True
        if method == "POST" and path == "/auth/logout":
            session = _session_from_request(headers, store)
            token = headers.get("x-nova-session") or _cookie_token(headers)
            if token:
                store.pop(token, None)
            await _send_json(send, 200, {"success": True, "logged_out": True, "session_removed": bool(session)}, cors, [_clear_cookie_header()])
            return True
        if method != "POST" or path not in {"/register", "/login"}:
            await _send_json(send, 405, {"success": False, "error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed."}}, cors)
            return True
        body = bytearray()
        while True:
            message = await receive()
            if message.get("type") != "http.request":
                continue
            body.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break
        try:
            payload = json.loads(bytes(body).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            await _send_json(send, 400, {"success": False, "error": {"code": "INVALID_JSON", "message": "Please provide valid JSON."}}, cors)
            return True
        email = str(payload.get("email", "")).strip().lower()
        password = payload.get("password", "")
        if not isinstance(password, str):
            password = str(password)
        try:
            if not email or not EMAIL_PATTERN.match(email):
                raise ValueError("Please provide a valid email address.")
            auth.validate_password(password)
            if path == "/register":
                from backend.age_policy import validate_minimum_age
                validate_minimum_age(payload.get("date_of_birth"))
        except (ValueError, TypeError) as exc:
            await _send_json(send, 400, {"success": False, "error": {"code": "INVALID_CREDENTIALS", "message": str(exc)}}, cors)
            return True
        if path == "/register":
            try:
                created = auth.register_user(email, password)
            except Exception:
                print("[BOOT REGISTER ERROR]", flush=True)
                traceback.print_exc()
                await _send_json(send, 500, {"success": False, "error": {"code": "REGISTRATION_ERROR", "message": "Registration failed."}}, cors)
                return True
            if not created:
                await _send_json(send, 409, {"success": False, "message": "An account with this email may already exist.", "email": email}, cors)
                return True
        else:
            try:
                valid = auth.login_user(email, password)
            except Exception:
                print("[BOOT LOGIN ERROR]", flush=True)
                traceback.print_exc()
                await _send_json(send, 500, {"success": False, "error": {"code": "LOGIN_ERROR", "message": "Login failed."}}, cors)
                return True
            if not valid:
                await _send_json(send, 401, {"success": False, "message": "Incorrect email or password.", "email": None}, cors)
                return True
        session = _new_session(email, store)
        await _send_json(send, 200, {"success": True, "email": email, "user": {"email": email}, "session": session}, cors, [_cookie_header(session["token"])])
        return True
    except Exception:
        print("[BOOT AUTH FALLBACK ERROR]", flush=True)
        traceback.print_exc()
        await _send_json(send, 503, {"success": False, "error": {"code": "AUTH_UNAVAILABLE", "message": "Nova authentication is temporarily unavailable."}}, _cors_headers(scope))
        return True


async def _handle_preflight(scope: dict[str, Any], send: Callable[..., Awaitable[Any]]) -> None:
    origin = _request_origin(scope)
    headers: list[tuple[bytes, bytes]] = [
        (b"access-control-allow-methods", b"GET, POST, PUT, PATCH, DELETE, OPTIONS"),
        (b"access-control-allow-headers", b"Authorization, Content-Type, X-Nova-Session, X-Request-ID"),
        (b"access-control-allow-credentials", b"true"),
        (b"access-control-max-age", b"600"),
        (b"vary", b"Origin"),
    ]
    if _origin_allowed(origin):
        headers.append((b"access-control-allow-origin", origin.encode("latin-1")))
        await _send_json(send, 204, {}, headers)
    else:
        await _send_json(send, 403, {"success": False, "error": {"code": "CORS_ORIGIN_DENIED", "message": "Origin is not allowed."}}, headers)


async def _send_to_real_app_with_cors(scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]], real_app: Any) -> None:
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
    await real_app(scope, receive, cors_send)


async def app(scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:
    scope_type = scope.get("type")
    if scope_type == "lifespan":
        await _handle_lifespan(receive, send)
        return
    if scope_type != "http":
        real_app = _load_real_app()
        await real_app(scope, receive, send)
        return
    path = scope.get("path", "/")
    method = scope.get("method", "GET").upper()
    if method == "OPTIONS":
        await _handle_preflight(scope, send)
        return
    if path == "/health":
        await _send_json(send, 200, {"success": True, "status": "healthy", "service": "nova-api", "version": "1.0.0"}, _cors_headers(scope))
        return
    if path == "/ready":
        required = ("NOVA_ENV", "NOVA_ALLOWED_ORIGINS")
        missing = [key for key in required if not os.getenv(key, "").strip()]
        if missing:
            await _send_json(send, 503, {"success": False, "status": "not_ready", "missing": missing}, _cors_headers(scope))
            return
        db_ok, db_error = _database_probe()
        llm_ok, llm_error = _openrouter_probe()
        if not db_ok or not llm_ok:
            checks: dict[str, str] = {}
            if not db_ok:
                checks["database"] = db_error or "unavailable"
            if not llm_ok:
                checks["openrouter"] = llm_error or "unavailable"
            await _send_json(send, 503, {"success": False, "status": "not_ready", "checks": checks}, _cors_headers(scope))
            return
        await _send_json(send, 200, {"success": True, "status": "ready", "service": "nova-api", "runtime": "lazy", "checks": {"database": "ok", "openrouter": "configured"}}, _cors_headers(scope))
        return
    if await _handle_auth_fallback(scope, receive, send):
        return
    if path == "/" and method == "GET":
        await _send_json(send, 200, {"name": "Nova AI", "status": "online", "version": "1.0.0", "api": "/api"}, _cors_headers(scope))
        return
    try:
        real_app = _load_real_app()
    except Exception:
        await _send_json(send, 503, {"success": False, "error": {"code": "PRODUCTION_APP_INIT_FAILED", "message": "Nova is temporarily unavailable while the application runtime starts."}}, _cors_headers(scope))
        return
    await _send_to_real_app_with_cors(scope, receive, send, real_app)
