import importlib

import pytest


@pytest.fixture
def production_module(monkeypatch, tmp_path):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.setenv("NOVA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NOVA_SESSION_DB", str(tmp_path / "sessions.sqlite3"))
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example.com")
    monkeypatch.delenv("NOVA_ENABLE_DOCS", raising=False)
    monkeypatch.delenv("NOVA_ENABLE_DEMO", raising=False)

    import backend.production as production

    module = importlib.reload(production)
    yield module


def test_production_requires_https_allowlist(monkeypatch, tmp_path):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.setenv("NOVA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NOVA_SESSION_DB", str(tmp_path / "sessions.sqlite3"))
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example.com")

    import backend.production as production

    production = importlib.reload(production)
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "http://localhost:5173")

    with pytest.raises(RuntimeError, match="non-HTTPS"):
        production._configured_origins()


def test_production_defaults_docs_and_demo_off(production_module):
    assert production_module.ENABLE_DOCS is False
    assert production_module.ENABLE_DEMO is False
    assert "/docs" not in production_module.PUBLIC_PATHS
    assert "/demo/session" not in production_module.PUBLIC_PATHS
    assert production_module.configured_origins == ["https://nova.example.com"]
