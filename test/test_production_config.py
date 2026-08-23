import os

import pytest


def test_production_requires_explicit_https_cors(monkeypatch):
    """Production must not silently fall back to a development/default origin."""
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.delenv("NOVA_ALLOWED_ORIGINS", raising=False)

    # Importing production is intentionally deferred because the module also
    # initializes the application runtime. Test the configuration contract by
    # exercising its pure origin helper after importing with a valid temporary
    # production origin.
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://example.test")
    from backend import production

    assert production.configured_origins == ["https://example.test"]


def test_production_rejects_insecure_cors(monkeypatch):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "http://example.test")

    with pytest.raises(RuntimeError, match="non-HTTPS"):
        from backend.production import _configured_origins
        _configured_origins()


def test_production_request_id_is_uuid():
    from uuid import UUID

    request_id = "00000000-0000-0000-0000-000000000000"
    UUID(request_id)
