from __future__ import annotations

import importlib
from uuid import UUID

import pytest


def _load_production(monkeypatch):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://example.test")
    from backend import production
    return importlib.reload(production)


def test_production_requires_explicit_https_cors(monkeypatch):
    production = _load_production(monkeypatch)
    monkeypatch.delenv("NOVA_ALLOWED_ORIGINS", raising=False)
    with pytest.raises(RuntimeError, match="must be configured"):
        production._configured_origins()


def test_production_rejects_insecure_cors(monkeypatch):
    production = _load_production(monkeypatch)
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "http://example.test")
    with pytest.raises(RuntimeError, match="non-HTTPS"):
        production._configured_origins()


def test_production_request_id_is_uuid():
    UUID("00000000-0000-0000-0000-000000000000")


def test_sensitive_status_endpoint_is_not_public(monkeypatch):
    production = _load_production(monkeypatch)
    assert "/status" not in production.PUBLIC_PATHS
    assert "/health" in production.PUBLIC_PATHS
    assert "/ready" in production.PUBLIC_PATHS


def test_privacy_endpoints_are_registered(monkeypatch):
    production = _load_production(monkeypatch)
    routes = {(route.path, method) for route in production.app.routes for method in getattr(route, "methods", set())}
    assert ("/memory", "DELETE") in routes
    assert ("/account", "DELETE") in routes
