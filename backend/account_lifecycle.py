from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from backend import auth


def _normalize_email(email: str) -> str:
    return str(email).strip().lower()


def _user_hash(email: str) -> str:
    return hashlib.sha256(_normalize_email(email).encode("utf-8")).hexdigest()


def _memory_user_dir(email: str) -> Path:
    return Path(os.getenv("NOVA_MEMORY_DIR", "data/memory/users")) / _user_hash(email)


def _settings_user_dir(email: str) -> Path:
    return Path(os.getenv("NOVA_USER_SETTINGS_DIR", "data/settings/users")) / _user_hash(email)


def clear_user_memory(email: str) -> bool:
    """Clear only the user's long-term memory, leaving account and chats intact."""
    memory_dir = _memory_user_dir(email)
    if not memory_dir.exists():
        return False
    shutil.rmtree(memory_dir)
    return True


def _remove_local_user(email: str) -> bool:
    path = auth.USERS_FILE
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    users = data.get("users", {})
    normalized = _normalize_email(email)
    keys = [key for key in users if _normalize_email(key) == normalized]
    if not keys:
        return False
    for key in keys:
        users.pop(key, None)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    return True


def _remove_database_user(email: str) -> bool:
    if not auth.DATABASE_URL:
        return False
    if not auth._ensure_database():
        # Authentication already marked the database unavailable. Do not call
        # _connect() again and turn an otherwise safe local cleanup into a 500.
        return False
    try:
        with auth._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM nova_users WHERE email = %s", (_normalize_email(email),))
                deleted = cur.rowcount > 0
            conn.commit()
        return deleted
    except Exception as error:
        raise RuntimeError("Nova could not remove the account from PostgreSQL safely.") from error


def _remove_sessions(email: str, session_store: Any) -> int:
    if session_store is None:
        return 0
    specialized = getattr(session_store, "delete_user_sessions", None)
    if callable(specialized):
        return int(specialized(email))
    removed = 0
    for token, session in list(session_store.items()):
        if isinstance(session, dict) and _normalize_email(session.get("email", "")) == _normalize_email(email):
            session_store.pop(token, None)
            removed += 1
    return removed


def delete_user_data(email: str, session_store: Any = None) -> dict[str, Any]:
    """Delete all user-owned application data currently persisted by Nova V1."""
    normalized = _normalize_email(email)
    deleted: dict[str, Any] = {
        "account": False,
        "sessions": 0,
        "memory": False,
        "conversations": False,
        "settings": False,
        "legacy_local_account": False,
    }

    db_deleted = _remove_database_user(normalized)
    local_deleted = _remove_local_user(normalized)
    deleted["account"] = db_deleted or local_deleted
    deleted["legacy_local_account"] = local_deleted
    deleted["sessions"] = _remove_sessions(normalized, session_store)
    deleted["memory"] = clear_user_memory(normalized)

    settings_dir = _settings_user_dir(normalized)
    if settings_dir.exists():
        shutil.rmtree(settings_dir)
        deleted["settings"] = True

    conversation_file = Path(os.getenv("NOVA_CONVERSATIONS_FILE", "data/memory/conversations.json"))
    if conversation_file.exists():
        try:
            data = json.loads(conversation_file.read_text(encoding="utf-8"))
            users = data.get("users", {})
            matching = [key for key in users if _normalize_email(key) == normalized]
            if matching:
                for key in matching:
                    users.pop(key, None)
                temporary = conversation_file.with_suffix(conversation_file.suffix + ".tmp")
                temporary.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
                temporary.replace(conversation_file)
                deleted["conversations"] = True
        except (OSError, ValueError) as error:
            raise RuntimeError("Nova could not safely remove persisted conversation data.") from error

    return deleted
