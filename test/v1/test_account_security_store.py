import json

from backend import account_security


def _use_local_store(monkeypatch, tmp_path):
    path = tmp_path / "account_security.json"
    monkeypatch.setattr(account_security, "SECURITY_FILE", path)
    monkeypatch.setattr(account_security, "_db_ready", lambda: False)
    return path


def test_security_store_recovers_from_non_mapping_root(monkeypatch, tmp_path):
    path = _use_local_store(monkeypatch, tmp_path)
    path.write_text(json.dumps(["not", "a", "mapping"]), encoding="utf-8")

    assert account_security._load_local() == {"users": {}}
    assert account_security._record("student@example.com") == {
        "email": "student@example.com",
        "email_verified": False,
    }


def test_security_store_filters_malformed_user_records(monkeypatch, tmp_path):
    path = _use_local_store(monkeypatch, tmp_path)
    path.write_text(json.dumps({
        "users": {
            "student@example.com": {"email_verified": True},
            "broken@example.com": "not-an-object",
        }
    }), encoding="utf-8")

    assert account_security._record("student@example.com")["email_verified"] is True
    assert account_security._record("broken@example.com") == {
        "email": "broken@example.com",
        "email_verified": False,
    }


def test_security_store_recovers_from_missing_users_collection(monkeypatch, tmp_path):
    path = _use_local_store(monkeypatch, tmp_path)
    path.write_text(json.dumps({"unexpected": []}), encoding="utf-8")

    account_security._save_record({
        "email": "student@example.com",
        "email_verified": True,
    })

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["users"]["student@example.com"]["email_verified"] is True


def test_security_store_handles_invalid_utf8_without_crashing(monkeypatch, tmp_path):
    path = _use_local_store(monkeypatch, tmp_path)
    path.write_bytes(b"\xff\xfe")

    assert account_security._record("student@example.com")["email_verified"] is False
