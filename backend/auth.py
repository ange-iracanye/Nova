from __future__ import annotations

import base64
import hashlib
import os
import secrets
import threading
import time
from pathlib import Path

import psycopg

DATA_DIR = Path(os.getenv("NOVA_DATA_DIR", "data"))
USERS_FILE = DATA_DIR / "users.json"
DATABASE_URL = os.getenv("NOVA_DATABASE_URL", "").strip()

PASSWORD_SCHEME = "scrypt"
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 1000
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 5

_login_failures: dict[str, list[float]] = {}
_LOGIN_LOCK = threading.RLock()
_USERS_LOCK = threading.RLock()
_DB_READY = False
_DB_LOCK = threading.RLock()


def validate_password(password: str) -> str:
    if not isinstance(password, str):
        raise ValueError("Password must be a string.")
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be between {PASSWORD_MIN_LENGTH} and {PASSWORD_MAX_LENGTH} characters.")
    return password


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=KEY_BYTES, maxmem=64 * 1024 * 1024)
    return "$".join([PASSWORD_SCHEME, str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P), _b64encode(salt), _b64encode(derived)])


def _verify_scrypt(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, digest_text = encoded.split("$", 5)
        if scheme != PASSWORD_SCHEME:
            return False
        expected = _b64decode(digest_text)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=_b64decode(salt_text), n=int(n), r=int(r), p=int(p), dklen=len(expected), maxmem=64 * 1024 * 1024)
        return secrets.compare_digest(actual, expected)
    except (TypeError, ValueError, OverflowError):
        return False


def verify_password(password: str, stored_hash: str) -> bool:
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False
    if stored_hash.startswith(f"{PASSWORD_SCHEME}$"):
        return _verify_scrypt(password, stored_hash)
    if len(stored_hash) == 64:
        return secrets.compare_digest(hashlib.sha256(password.encode("utf-8")).hexdigest(), stored_hash)
    return False


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _ensure_database() -> None:
    global _DB_READY
    if not DATABASE_URL or _DB_READY:
        return
    with _DB_LOCK:
        if _DB_READY:
            return
        try:
            with psycopg.connect(DATABASE_URL, connect_timeout=10) as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE TABLE IF NOT EXISTS nova_users (email TEXT PRIMARY KEY, password TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
                conn.commit()
            _DB_READY = True
        except Exception as error:
            raise RuntimeError("Nova could not connect to the configured PostgreSQL database.") from error


def _load_file_users() -> dict:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        return {"users": {}}
    try:
        import json
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and isinstance(data.get("users"), dict) else {"users": {}}
    except (OSError, ValueError):
        raise RuntimeError("Nova local user database could not be read safely.")


def _save_file_users(data: dict) -> None:
    import json
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_users() -> dict:
    with _USERS_LOCK:
        if not DATABASE_URL:
            return _load_file_users()
        _ensure_database()
        try:
            with psycopg.connect(DATABASE_URL, connect_timeout=10) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT email, password FROM nova_users")
                    rows = cur.fetchall()
            return {"users": {email: {"email": email, "password": password} for email, password in rows}}
        except Exception as error:
            raise RuntimeError("Nova user database could not be read from PostgreSQL.") from error


def save_users(data: dict) -> None:
    with _USERS_LOCK:
        if not DATABASE_URL:
            _save_file_users(data)
            return
        _ensure_database()
        try:
            with psycopg.connect(DATABASE_URL, connect_timeout=10) as conn:
                with conn.cursor() as cur:
                    for email, user in data.get("users", {}).items():
                        password = user.get("password") if isinstance(user, dict) else None
                        if password:
                            cur.execute("INSERT INTO nova_users (email, password) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET password = EXCLUDED.password", (email, password))
                conn.commit()
        except Exception as error:
            raise RuntimeError("Nova user database could not be written to PostgreSQL.") from error


def _prune_login_failures(email: str, now: float) -> list[float]:
    with _LOGIN_LOCK:
        attempts = [t for t in _login_failures.get(email, []) if now - t < LOGIN_WINDOW_SECONDS]
        if attempts:
            _login_failures[email] = attempts
        else:
            _login_failures.pop(email, None)
        return attempts


def is_login_throttled(email: str) -> bool:
    return len(_prune_login_failures(_normalize_email(email), time.monotonic())) >= LOGIN_MAX_FAILURES


def _record_login_failure(email: str) -> None:
    email = _normalize_email(email)
    now = time.monotonic()
    with _LOGIN_LOCK:
        _login_failures[email] = _prune_login_failures(email, now) + [now]


def _clear_login_failures(email: str) -> None:
    with _LOGIN_LOCK:
        _login_failures.pop(_normalize_email(email), None)


def register_user(email: str, password: str) -> bool:
    email = _normalize_email(email)
    validate_password(password)
    with _USERS_LOCK:
        data = load_users()
        if email in data["users"]:
            return False
        data["users"][email] = {"email": email, "password": hash_password(password)}
        save_users(data)
    return True


def login_user(email: str, password: str) -> bool:
    email = _normalize_email(email)
    if is_login_throttled(email):
        return False
    with _USERS_LOCK:
        data = load_users()
        user = data["users"].get(email)
        if not isinstance(user, dict):
            _record_login_failure(email)
            return False
        stored_hash = user.get("password")
        if not verify_password(password, stored_hash):
            _record_login_failure(email)
            return False
        _clear_login_failures(email)
        if isinstance(stored_hash, str) and not stored_hash.startswith(f"{PASSWORD_SCHEME}$"):
            user["password"] = hash_password(password)
            save_users(data)
        return True
