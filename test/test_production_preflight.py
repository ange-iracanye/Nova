from __future__ import annotations

import pytest

from scripts.production_preflight import main


def _production_env(monkeypatch):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example")
    monkeypatch.setenv("NOVA_DATABASE_URL", "postgresql://user:pass@example/db")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("NOVA_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("NOVA_LLM_MODEL", "nvidia/nemotron-3-ultra:free")
    monkeypatch.setenv("NOVA_LLM_FALLBACK_MODEL", "openrouter/free")
    monkeypatch.setenv("NOVA_ENABLE_DEMO", "false")
    monkeypatch.setenv("NOVA_ENABLE_DOCS", "false")


def test_preflight_accepts_v1_configuration(monkeypatch):
    _production_env(monkeypatch)
    assert main() == 0


def test_preflight_rejects_paid_primary_model(monkeypatch):
    _production_env(monkeypatch)
    monkeypatch.setenv("NOVA_LLM_MODEL", "some/provider:paid")
    with pytest.raises(SystemExit, match="COST SAFETY FAILURE"):
        main()


def test_preflight_rejects_public_demo(monkeypatch):
    _production_env(monkeypatch)
    monkeypatch.setenv("NOVA_ENABLE_DEMO", "true")
    with pytest.raises(SystemExit, match="PUBLIC DEMO"):
        main()


def test_preflight_requires_https(monkeypatch):
    _production_env(monkeypatch)
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "http://nova.example")
    with pytest.raises(SystemExit, match="non-HTTPS"):
        main()
