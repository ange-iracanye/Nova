from __future__ import annotations

import hashlib
import os
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from backend import auth

TOKEN_TTL = timedelta(hours=24)
RESET_TTL = timedelta(hours=1)
SECURITY_FILE = Path(os.getenv("NOVA_DATA_DIR", "data")) / "account_security.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _email(email: str) -> str:
    return str(email).strip().lower()


def _load_local() -> dict[str, Any]:
    SECURITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SECURITY_FILE.exists():
        return {"users": {}}
    try:
        import json
        value = json.loads(SECURITY_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {"users": {}}
    except (OSError, ValueError):
        return {"users": {}}


def _save_local(value: dict[str, Any]) -> None:
    import json
    SECURITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = SECURITY_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(SECURITY_FILE)


def _db_ready() -> bool:
    return bool(auth.DATABASE_URL and auth._ensure_database())


def _ensure_db() -> None:
    if not _db_ready():
        return
    with auth._connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS nova_account_security (
                    email TEXT PRIMARY KEY,
                    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
                    verification_token_hash TEXT,
                    verification_expires_at TIMESTAMPTZ,
                    reset_token_hash TEXT,
                    reset_expires_at TIMESTAMPTZ,
                    email_change_target TEXT,
                    email_change_token_hash TEXT,
                    email_change_expires_at TIMESTAMPTZ
                )
                """
            )
        conn.commit()


def _record(email: str) -> dict[str, Any]:
    email = _email(email)
    if _db_ready():
        _ensure_db()
        with auth._connect() as conn:
            row = conn.execute(
                "SELECT email, email_verified, verification_token_hash, verification_expires_at, reset_token_hash, reset_expires_at, email_change_target, email_change_token_hash, email_change_expires_at FROM nova_account_security WHERE email = %s",
                (email,),
            ).fetchone()
        if row:
            return {
                "email": row[0], "email_verified": bool(row[1]),
                "verification_token_hash": row[2], "verification_expires_at": row[3],
                "reset_token_hash": row[4], "reset_expires_at": row[5],
                "email_change_target": row[6], "email_change_token_hash": row[7], "email_change_expires_at": row[8],
            }
        return {"email": email, "email_verified": False}
    data = _load_local()["users"]
    return dict(data.get(email) or {"email": email, "email_verified": False})


def _save_record(record: dict[str, Any]) -> None:
    email = _email(record["email"])
    if _db_ready():
        _ensure_db()
        with auth._connect() as conn:
            conn.execute(
                """
                INSERT INTO nova_account_security(email, email_verified, verification_token_hash, verification_expires_at, reset_token_hash, reset_expires_at, email_change_target, email_change_token_hash, email_change_expires_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(email) DO UPDATE SET
                    email_verified=EXCLUDED.email_verified,
                    verification_token_hash=EXCLUDED.verification_token_hash,
                    verification_expires_at=EXCLUDED.verification_expires_at,
                    reset_token_hash=EXCLUDED.reset_token_hash,
                    reset_expires_at=EXCLUDED.reset_expires_at,
                    email_change_target=EXCLUDED.email_change_target,
                    email_change_token_hash=EXCLUDED.email_change_token_hash,
                    email_change_expires_at=EXCLUDED.email_change_expires_at
                """,
                (email, bool(record.get("email_verified")), record.get("verification_token_hash"), record.get("verification_expires_at"), record.get("reset_token_hash"), record.get("reset_expires_at"), record.get("email_change_target"), record.get("email_change_token_hash"), record.get("email_change_expires_at")),
            )
            conn.commit()
        return
    data = _load_local()
    data.setdefault("users", {})[email] = record
    _save_local(data)


def _smtp_configured() -> bool:
    return bool(os.getenv("NOVA_SMTP_HOST", "").strip() and os.getenv("NOVA_SMTP_FROM", "").strip())


def _send_email(to: str, subject: str, body: str) -> bool:
    host = os.getenv("NOVA_SMTP_HOST", "").strip()
    sender = os.getenv("NOVA_SMTP_FROM", "").strip()
    if not host or not sender:
        if os.getenv("NOVA_ENV", "development").strip().lower() != "production":
            print(f"[Nova account security] {subject} for {to}:\n{body}", flush=True)
            return True
        return False
    port = int(os.getenv("NOVA_SMTP_PORT", "587"))
    username = os.getenv("NOVA_SMTP_USER", "").strip()
    password = os.getenv("NOVA_SMTP_PASSWORD", "")
    use_ssl = os.getenv("NOVA_SMTP_SSL", "false").strip().lower() == "true"
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=15) as server:
                if username:
                    server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.ehlo()
                if os.getenv("NOVA_SMTP_STARTTLS", "true").strip().lower() == "true":
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                if username:
                    server.login(username, password)
                server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        print(f"[Nova account security] email delivery failed: {type(exc).__name__}: {exc}", flush=True)
        return False


def status(email: str) -> dict[str, Any]:
    record = _record(email)
    pending = bool(record.get("email_change_target"))
    return {"email": _email(email), "email_verified": bool(record.get("email_verified")), "email_change_pending": pending}


def issue_verification(email: str) -> bool:
    email = _email(email)
    token = secrets.token_urlsafe(48)
    record = _record(email)
    record.update({"email": email, "verification_token_hash": _hash(token), "verification_expires_at": _now() + TOKEN_TTL})
    _save_record(record)
    base = os.getenv("NOVA_PUBLIC_FRONTEND_URL", "https://nova-frontend-i76e.onrender.com").rstrip("/")
    return _send_email(email, "Verify your Nova email", f"Verify your Nova account:\n\n{base}/verify-email?token={token}\n\nThis link expires in 24 hours.")


def verify_email(token: str) -> str | None:
    token_hash = _hash(str(token).strip())
    now = _now()
    for email in _all_security_emails():
        record = _record(email)
        expires = record.get("verification_expires_at")
        if record.get("verification_token_hash") == token_hash and expires and _as_datetime(expires) > now:
            record["email_verified"] = True
            record["verification_token_hash"] = None
            record["verification_expires_at"] = None
            _save_record(record)
            return email
    return None


def request_reset(email: str) -> bool:
    email = _email(email)
    if not _user_exists(email):
        return True
    token = secrets.token_urlsafe(48)
    record = _record(email)
    record.update({"email": email, "reset_token_hash": _hash(token), "reset_expires_at": _now() + RESET_TTL})
    _save_record(record)
    base = os.getenv("NOVA_PUBLIC_FRONTEND_URL", "https://nova-frontend-i76e.onrender.com").rstrip("/")
    return _send_email(email, "Reset your Nova password", f"Reset your Nova password:\n\n{base}/reset-password?token={token}\n\nThis link expires in 1 hour. If you did not request this, you can ignore this email.")


def reset_password(token: str, new_password: str) -> str | None:
    auth.validate_password(new_password)
    token_hash = _hash(str(token).strip())
    now = _now()
    for email in _all_security_emails():
        record = _record(email)
        expires = record.get("reset_expires_at")
        if record.get("reset_token_hash") == token_hash and expires and _as_datetime(expires) > now:
            _set_password(email, new_password)
            record["reset_token_hash"] = None
            record["reset_expires_at"] = None
            _save_record(record)
            return email
    return None


def change_password(email: str, current_password: str, new_password: str) -> bool:
    if not auth.login_user(email, current_password):
        return False
    auth.validate_password(new_password)
    _set_password(email, new_password)
    return True


def request_email_change(email: str, new_email: str) -> bool:
    email = _email(email)
    new_email = _email(new_email)
    if new_email == email or not _email_available(new_email):
        return False
    token = secrets.token_urlsafe(48)
    record = _record(email)
    record.update({"email_change_target": new_email, "email_change_token_hash": _hash(token), "email_change_expires_at": _now() + TOKEN_TTL})
    _save_record(record)
    base = os.getenv("NOVA_PUBLIC_FRONTEND_URL", "https://nova-frontend-i76e.onrender.com").rstrip("/")
    return _send_email(new_email, "Confirm your Nova email change", f"Confirm your new Nova email address:\n\n{base}/confirm-email-change?token={token}\n\nThis link expires in 24 hours.")


def confirm_email_change(token: str) -> tuple[str, str] | None:
    token_hash = _hash(str(token).strip())
    now = _now()
    for old_email in _all_security_emails():
        record = _record(old_email)
        expires = record.get("email_change_expires_at")
        if record.get("email_change_token_hash") == token_hash and expires and _as_datetime(expires) > now:
            new_email = _email(record.get("email_change_target"))
            if not new_email or not _email_available(new_email):
                return None
            _migrate_account(old_email, new_email)
            record = {"email": new_email, "email_verified": True}
            _save_record(record)
            _delete_security_record(old_email)
            return old_email, new_email
    return None


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _all_security_emails() -> list[str]:
    if _db_ready():
        _ensure_db()
        with auth._connect() as conn:
            rows = conn.execute("SELECT email FROM nova_account_security").fetchall()
        return [str(row[0]).lower() for row in rows]
    return list(_load_local().get("users", {}).keys())


def _user_exists(email: str) -> bool:
    try:
        return auth._db_get_user(email) is not None if _db_ready() else email in _load_local_users()
    except Exception:
        return False


def _load_local_users() -> dict[str, Any]:
    return auth._load_file_users().get("users", {})


def _email_available(email: str) -> bool:
    return not _user_exists(email)


def _set_password(email: str, password: str) -> None:
    hashed = auth.hash_password(password)
    if _db_ready():
        auth._db_update_password(email, hashed)
        return
    data = auth._load_file_users()
    if email not in data.get("users", {}):
        raise ValueError("Account not found.")
    data["users"][email]["password"] = hashed
    auth._save_file_users(data)


def _delete_security_record(email: str) -> None:
    if _db_ready():
        _ensure_db()
        with auth._connect() as conn:
            conn.execute("DELETE FROM nova_account_security WHERE email = %s", (_email(email),))
            conn.commit()
        return
    data = _load_local()
    data.get("users", {}).pop(_email(email), None)
    _save_local(data)


def _migrate_account(old_email: str, new_email: str) -> None:
    old_email, new_email = _email(old_email), _email(new_email)
    if _db_ready():
        _ensure_db()
        with auth._connect() as conn:
            cur = conn.execute("UPDATE nova_users SET email = %s WHERE email = %s", (new_email, old_email))
            if cur.rowcount != 1:
                raise ValueError("Account could not be migrated.")
            conn.commit()
    else:
        data = auth._load_file_users()
        user = data.get("users", {}).pop(old_email, None)
        if not user:
            raise ValueError("Account could not be migrated.")
        user["email"] = new_email
        data["users"][new_email] = user
        auth._save_file_users(data)

    _migrate_json_conversations(old_email, new_email)
    for root_env in ("NOVA_MEMORY_DIR", "NOVA_USER_SETTINGS_DIR"):
        root = Path(os.getenv(root_env, "data/memory/users" if "MEMORY" in root_env else "data/settings/users"))
        old_dir = root / hashlib.sha256(old_email.encode()).hexdigest()
        new_dir = root / hashlib.sha256(new_email.encode()).hexdigest()
        if old_dir.exists() and not new_dir.exists():
            new_dir.parent.mkdir(parents=True, exist_ok=True)
            old_dir.rename(new_dir)


def _migrate_json_conversations(old_email: str, new_email: str) -> None:
    import json
    path = Path(os.getenv("NOVA_CONVERSATIONS_FILE", "data/memory/conversations.json"))
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        users = data.get("users", {})
        if old_email in users:
            users[new_email] = users.pop(old_email)
            path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    except (OSError, ValueError):
        raise RuntimeError("Conversation data could not be migrated safely.")


def register_routes(app: Any) -> None:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.get("/auth/status", tags=["Authentication"])
    def auth_status(request: Request):
        from backend import api
        session = api.get_auth_session(request)
        if not session:
            return JSONResponse(status_code=401, content={"success": False, "error": {"code": "NOT_AUTHENTICATED", "message": "A valid Nova session is required."}})
        return {"success": True, **status(session["email"])}

    @app.post("/auth/request-verification", tags=["Authentication"])
    def request_verification(request: Request):
        from backend import api
        session = api.get_auth_session(request)
        if not session:
            return JSONResponse(status_code=401, content={"success": False, "error": {"code": "NOT_AUTHENTICATED", "message": "A valid Nova session is required."}})
        if status(session["email"])["email_verified"]:
            return {"success": True, "already_verified": True}
        if not issue_verification(session["email"]):
            return JSONResponse(status_code=503, content={"success": False, "error": {"code": "EMAIL_DELIVERY_UNAVAILABLE", "message": "Email delivery is not configured or is temporarily unavailable."}})
        return {"success": True, "verification_sent": True}

    @app.post("/auth/verify-email", tags=["Authentication"])
    async def verify_email_endpoint(request: Request):
        payload = await request.json()
        email = verify_email(str(payload.get("token", "")))
        if not email:
            return JSONResponse(status_code=400, content={"success": False, "error": {"code": "INVALID_VERIFICATION_TOKEN", "message": "The verification link is invalid or expired."}})
        return {"success": True, "email": email, "email_verified": True}

    @app.post("/auth/forgot-password", tags=["Authentication"])
    async def forgot_password(request: Request):
        payload = await request.json()
        email = _email(payload.get("email", ""))
        if not email:
            return JSONResponse(status_code=400, content={"success": False, "error": {"code": "INVALID_EMAIL", "message": "Please provide a valid email address."}})
        if not request_reset(email):
            return JSONResponse(status_code=503, content={"success": False, "error": {"code": "EMAIL_DELIVERY_UNAVAILABLE", "message": "Email delivery is not configured or is temporarily unavailable."}})
        return {"success": True, "message": "If an account exists for that email, a password reset link has been sent."}

    @app.post("/auth/reset-password", tags=["Authentication"])
    async def reset_password_endpoint(request: Request):
        payload = await request.json()
        email = reset_password(str(payload.get("token", "")), str(payload.get("password", "")))
        if not email:
            return JSONResponse(status_code=400, content={"success": False, "error": {"code": "INVALID_RESET_TOKEN", "message": "The reset link is invalid or expired."}})
        return {"success": True, "password_reset": True, "email": email}

    @app.post("/auth/change-password", tags=["Authentication"])
    async def change_password_endpoint(request: Request):
        from backend import api
        session = api.get_auth_session(request)
        if not session:
            return JSONResponse(status_code=401, content={"success": False, "error": {"code": "NOT_AUTHENTICATED", "message": "A valid Nova session is required."}})
        payload = await request.json()
        try:
            changed = change_password(session["email"], str(payload.get("current_password", "")), str(payload.get("new_password", "")))
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"success": False, "error": {"code": "INVALID_PASSWORD", "message": str(exc)}})
        if not changed:
            return JSONResponse(status_code=401, content={"success": False, "error": {"code": "CURRENT_PASSWORD_INVALID", "message": "The current password is incorrect."}})
        return {"success": True, "password_changed": True}

    @app.post("/auth/request-email-change", tags=["Authentication"])
    async def request_email_change_endpoint(request: Request):
        from backend import api
        session = api.get_auth_session(request)
        if not session:
            return JSONResponse(status_code=401, content={"success": False, "error": {"code": "NOT_AUTHENTICATED", "message": "A valid Nova session is required."}})
        payload = await request.json()
        new_email = _email(payload.get("new_email", ""))
        if not new_email or "@" not in new_email:
            return JSONResponse(status_code=400, content={"success": False, "error": {"code": "INVALID_EMAIL", "message": "Please provide a valid new email address."}})
        if not request_email_change(session["email"], new_email):
            return JSONResponse(status_code=409, content={"success": False, "error": {"code": "EMAIL_UNAVAILABLE", "message": "That email address is unavailable or already in use."}})
        return {"success": True, "confirmation_sent": True}

    @app.post("/auth/confirm-email-change", tags=["Authentication"])
    async def confirm_email_change_endpoint(request: Request):
        payload = await request.json()
        result = confirm_email_change(str(payload.get("token", "")))
        if not result:
            return JSONResponse(status_code=400, content={"success": False, "error": {"code": "INVALID_EMAIL_CHANGE_TOKEN", "message": "The email-change link is invalid or expired."}})
        return {"success": True, "email_changed": True, "old_email": result[0], "email": result[1]}

    _ensure_db()
