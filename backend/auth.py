from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import tempfile
import threading
from pathlib import Path


USERS_FILE = Path("data/users.json")

# Passwords are intentionally hashed with the Python standard library so
# Nova does not need a second password-hashing dependency just for V1.
# The encoded format is versioned so the algorithm can be upgraded later.
PASSWORD_SCHEME = "scrypt"
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32

_USERS_LOCK = threading.RLock()


def _empty_users() -> dict:
    return {"users": {}}


def _validate_users(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("User database must be a JSON object.")

    users = data.get("users")
    if not isinstance(users, dict):
        raise ValueError("User database is missing a valid 'users' object.")

    return data


def load_users() -> dict:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _USERS_LOCK:
        if not USERS_FILE.exists():
            return _empty_users()

        try:
            data = json.loads(
                USERS_FILE.read_text(encoding="utf-8")
            )
            return _validate_users(data)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            # Never silently replace a corrupted authentication database.
            # Returning an empty database here could make a later registration
            # overwrite the account state and is unsafe for production use.
            raise RuntimeError(
                "Nova user database could not be read safely."
            ) from error


def save_users(data: dict) -> None:
    _validate_users(data)
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(
        data,
        indent=4,
        ensure_ascii=False,
    )

    with _USERS_LOCK:
        fd, temporary_name = tempfile.mkstemp(
            prefix="users-",
            suffix=".json.tmp",
            dir=USERS_FILE.parent,
            text=True,
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())

            try:
                os.chmod(temporary_name, 0o600)
            except OSError:
                pass

            os.replace(temporary_name, USERS_FILE)
        finally:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    """Return a versioned, salted scrypt password hash."""
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_BYTES,
        maxmem=64 * 1024 * 1024,
    )

    return "$".join(
        [
            PASSWORD_SCHEME,
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            _b64encode(salt),
            _b64encode(derived),
        ]
    )


def _verify_scrypt(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, digest_text = encoded.split("$", 5)
        if scheme != PASSWORD_SCHEME:
            return False

        n_value = int(n)
        r_value = int(r)
        p_value = int(p)
        salt = _b64decode(salt_text)
        expected = _b64decode(digest_text)

        if not salt or not expected:
            return False

        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n_value,
            r=r_value,
            p=p_value,
            dklen=len(expected),
            maxmem=64 * 1024 * 1024,
        )

        return secrets.compare_digest(actual, expected)
    except (TypeError, ValueError, OverflowError):
        return False


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify both current scrypt hashes and legacy V1 SHA-256 hashes."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    if stored_hash.startswith(f"{PASSWORD_SCHEME}$"):
        return _verify_scrypt(password, stored_hash)

    # Backward compatibility for accounts created before production
    # hardening. Successful legacy logins are upgraded immediately.
    if len(stored_hash) == 64:
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return secrets.compare_digest(legacy, stored_hash)

    return False


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(email: str, password: str) -> bool:
    email = _normalize_email(email)

    with _USERS_LOCK:
        data = load_users()

        if email in data["users"]:
            return False

        data["users"][email] = {
            "email": email,
            "password": hash_password(password),
        }

        save_users(data)

    return True


def login_user(email: str, password: str) -> bool:
    email = _normalize_email(email)

    with _USERS_LOCK:
        data = load_users()
        user = data["users"].get(email)

        if not isinstance(user, dict):
            return False

        stored_hash = user.get("password")
        if not verify_password(password, stored_hash):
            return False

        # Transparently migrate old SHA-256 hashes after a successful login.
        if isinstance(stored_hash, str) and not stored_hash.startswith(
            f"{PASSWORD_SCHEME}$"
        ):
            user["password"] = hash_password(password)
            save_users(data)

        return True
