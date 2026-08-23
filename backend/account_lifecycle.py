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


def _memory_user_dir(email: str) -> Path:
    user_id = hashlib.sha256(_normalize_email(email).encode("utf-8")).hexdigest()
    return Path(os.getenv("NOVA_MEMORY_DIR", "data/memory/users")) / user_id


def clear_user_memory(email: str) -> bool:
    """Clear only the user's long-term memory, leaving the account and chats intact."""
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
    auth._ensure_database()
    with auth._connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM nova_users WHERE email = %s", (_normalize_email(email),))
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted


def delete_user_data(email: str, session_store: Any = None) -> dict[str, Any]:
    """Delete user-owned data currently persisted by Nova V1."""
    normalized = _normalize_email(email)
    deleted: dict[str, Any] = {
        "account": False,
        "sessions": 0,
        "memory": False,
        "conversations": False,
    }

    deleted["account"] = _remove_database_user(normalized) or _remove_local_user(normalized)

    if session_store is not None:
        for token, session in list(session_store.items()):
            if isinstance(session, dict) and _normalize_email(session.get("email", "")) == normalized:
                session_store.pop(token, None)
                deleted["sessions"] += 1

    deleted["memory"] = clear_user_memory(normalized)

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
