from __future__ import annotations

import hashlib
import json


def test_delete_user_data_removes_account_sessions_memory_and_conversations(tmp_path, monkeypatch):
    from backend import auth
    from backend.account_lifecycle import delete_user_data

    users_file = tmp_path / "users.json"
    memory_root = tmp_path / "memory" / "users"
    conversation_file = tmp_path / "conversations.json"

    monkeypatch.setattr(auth, "USERS_FILE", users_file)
    monkeypatch.setenv("NOVA_MEMORY_DIR", str(memory_root))
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", str(conversation_file))
    monkeypatch.setattr(auth, "DATABASE_URL", "")

    email = "student@example.com"
    users_file.parent.mkdir(parents=True, exist_ok=True)
    users_file.write_text(json.dumps({"users": {email: {"email": email, "password": "hash"}}}), encoding="utf-8")

    user_dir = memory_root / hashlib.sha256(email.encode()).hexdigest()
    user_dir.mkdir(parents=True)
    (user_dir / "semantic_memory.json").write_text("{}", encoding="utf-8")

    conversation_file.parent.mkdir(parents=True, exist_ok=True)
    conversation_file.write_text(json.dumps({"users": {email: {"conversations": {"abc": {"messages": []}}}}}), encoding="utf-8")

    class SessionStore(dict):
        pass

    store = SessionStore({
        "token-a": {"email": email, "expires_at": "2099-01-01T00:00:00+00:00"},
        "token-b": {"email": "other@example.com", "expires_at": "2099-01-01T00:00:00+00:00"},
    })
    result = delete_user_data(email, store)

    assert result["account"] is True
    assert result["sessions"] == 1
    assert result["memory"] is True
    assert result["conversations"] is True
    assert email not in json.loads(users_file.read_text(encoding="utf-8"))["users"]
    assert not user_dir.exists()
    assert email not in json.loads(conversation_file.read_text(encoding="utf-8"))["users"]
    assert "token-a" not in store
    assert "token-b" in store


def test_clear_user_memory_keeps_account_and_conversations(tmp_path, monkeypatch):
    from backend import auth
    from backend.account_lifecycle import clear_user_memory

    memory_root = tmp_path / "memory" / "users"
    monkeypatch.setenv("NOVA_MEMORY_DIR", str(memory_root))
    monkeypatch.setattr(auth, "DATABASE_URL", "")

    email = "student@example.com"
    user_dir = memory_root / hashlib.sha256(email.encode()).hexdigest()
    user_dir.mkdir(parents=True)
    (user_dir / "semantic_memory.json").write_text("{}", encoding="utf-8")

    assert clear_user_memory(email) is True
    assert not user_dir.exists()
    assert clear_user_memory(email) is False
