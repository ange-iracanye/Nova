from __future__ import annotations

import os
from pathlib import Path


def test_production_entrypoint_imports():
    os.environ.setdefault("NOVA_ENV", "test")
    os.environ.setdefault("NOVA_DATA_DIR", str(Path(".nova-test-data")))
    os.environ.setdefault("NOVA_SESSION_DB", str(Path(".nova-test-data") / "sessions.sqlite3"))

    from backend.production import app

    assert app.title == "Nova AI"
    assert any(route.path == "/health" for route in app.routes)
    assert any(route.path == "/auth/me" for route in app.routes)


def test_persistent_session_round_trip(tmp_path):
    from backend.persistent_sessions import PersistentSessionStore

    store = PersistentSessionStore(str(tmp_path / "sessions.sqlite3"))
    value = {
        "token": "test-token",
        "email": "test@example.com",
        "created_at": "2026-01-01T00:00:00+00:00",
        "last_seen": "2026-01-01T00:00:00+00:00",
        "expires_at": "2099-01-01T00:00:00+00:00",
    }

    store["test-token"] = value
    assert store["test-token"]["email"] == "test@example.com"

    reopened = PersistentSessionStore(str(tmp_path / "sessions.sqlite3"))
    assert reopened["test-token"]["email"] == "test@example.com"

    reopened.pop("test-token")
    assert reopened.get("test-token") is None
