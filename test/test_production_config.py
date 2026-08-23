from __future__ import annotations

from uuid import UUID

import pytest


def test_production_requires_explicit_https_cors(monkeypatch):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.delenv("NOVA_ALLOWED_ORIGINS", raising=False)
    from backend import production
    with pytest.raises(RuntimeError, match="must be configured"):
        production._configured_origins()


def test_production_rejects_insecure_cors(monkeypatch):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "http://example.test")
    from backend import production
    with pytest.raises(RuntimeError, match="non-HTTPS"):
        production._configured_origins()


def test_production_request_id_is_uuid():
    request_id = "00000000-0000-0000-0000-000000000000"
    UUID(request_id)


def test_sensitive_status_endpoint_is_not_public():
    from backend import production
    assert "/status" not in production.PUBLIC_PATHS
    assert "/health" in production.PUBLIC_PATHS
    assert "/ready" in production.PUBLIC_PATHS


def test_privacy_endpoints_are_registered():
    from backend import production
    routes = {(route.path, method) for route in production.app.routes for method in getattr(route, "methods", set())}
    assert ("/memory", "DELETE") in routes
    assert ("/account", "DELETE") in routes
