from __future__ import annotations

import json

from backend.account_lifecycle import _remove_local_user


def test_local_account_removal_ignores_malformed_json_without_overwriting(tmp_path, monkeypatch):
    from backend import auth

    path = tmp_path / "users.json"
    path.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(auth, "USERS_FILE", path)

    assert _remove_local_user("student@example.com") is False
    assert path.read_text(encoding="utf-8") == "{broken"


def test_local_account_removal_rejects_non_mapping_user_store(tmp_path, monkeypatch):
    from backend import auth

    path = tmp_path / "users.json"
    path.write_text(json.dumps({"users": ["not", "a", "mapping"]}), encoding="utf-8")
    monkeypatch.setattr(auth, "USERS_FILE", path)

    assert _remove_local_user("student@example.com") is False
    assert json.loads(path.read_text(encoding="utf-8")) == {"users": ["not", "a", "mapping"]}


def test_local_account_removal_recovers_from_invalid_utf8(tmp_path, monkeypatch):
    from backend import auth

    path = tmp_path / "users.json"
    path.write_bytes(b"\xff\xfe")
    monkeypatch.setattr(auth, "USERS_FILE", path)

    assert _remove_local_user("student@example.com") is False
    assert path.read_bytes() == b"\xff\xfe"
