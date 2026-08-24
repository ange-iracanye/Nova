import asyncio
import json

from backend.boot import app


def _run_request(path: str, environ=None):
    environ = environ or {}
    messages = [
        {"type": "http.request", "body": b"", "more_body": False}
    ]
    sent = []

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [
            (b"host", b"testserver"),
            *[(key.lower().encode(), value.encode()) for key, value in environ.items()],
        ],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
        "root_path": "",
        "http_version": "1.1",
    }

    asyncio.run(app(scope, receive, send))
    return sent


def test_health_does_not_load_full_runtime():
    sent = _run_request("/health")
    assert sent[0]["status"] == 200
    body = sent[1]["body"]
    payload = json.loads(body.decode())
    assert payload["status"] == "healthy"


def test_ready_requires_production_configuration(monkeypatch):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.delenv("NOVA_ALLOWED_ORIGINS", raising=False)
    sent = _run_request("/ready")
    assert sent[0]["status"] == 503
    payload = json.loads(sent[1]["body"].decode())
    assert "NOVA_ALLOWED_ORIGINS" in payload["missing"]


def test_ready_reports_database_failure_without_leaking_credentials(monkeypatch):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example")
    monkeypatch.setenv("NOVA_DATABASE_URL", "postgresql://postgres:super-secret@example.test/db")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("backend.boot._database_probe", lambda: (False, "PostgreSQL connectivity/authentication failed"))
    sent = _run_request("/ready")
    assert sent[0]["status"] == 503
    body = sent[1]["body"].decode()
    assert "super-secret" not in body
    payload = json.loads(body)
    assert payload["checks"]["database"] == "PostgreSQL connectivity/authentication failed"


def test_ready_succeeds_when_production_dependencies_are_available(monkeypatch):
    monkeypatch.setenv("NOVA_ENV", "production")
    monkeypatch.setenv("NOVA_ALLOWED_ORIGINS", "https://nova.example")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("backend.boot._database_probe", lambda: (True, None))
    sent = _run_request("/ready")
    assert sent[0]["status"] == 200
    payload = json.loads(sent[1]["body"].decode())
    assert payload["checks"]["database"] == "ok"
    assert payload["checks"]["openrouter"] == "configured"
