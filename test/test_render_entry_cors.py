import backend.render_entry as render_entry


def test_configured_https_origin_is_allowed(monkeypatch):
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example.com")
    assert render_entry._origin_is_allowed("https://nova.example.com")


def test_unconfigured_https_origin_is_rejected(monkeypatch):
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example.com")
    assert not render_entry._origin_is_allowed("https://unrelated.example")


def test_unconfigured_http_origin_is_rejected(monkeypatch):
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example.com")
    assert not render_entry._origin_is_allowed("http://localhost:5173")


def test_public_frontend_origin_remains_allowed(monkeypatch):
    monkeypatch.delenv("NOVA_ALLOWED_ORIGINS", raising=False)
    assert render_entry._origin_is_allowed(render_entry.PUBLIC_FRONTEND_ORIGIN)


def test_untrusted_origin_receives_no_cors_headers(monkeypatch):
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example.com")
    scope = {"headers": [(b"origin", b"https://unrelated.example")]}
    assert render_entry._cors_headers(scope) == []
