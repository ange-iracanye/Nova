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
