from backend import analytics


class FakeConnection:
    def __init__(self):
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params):
        self.params = params

    def commit(self):
        pass


def test_record_event_normalizes_missing_event_and_email(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(analytics, "DATABASE_URL", "postgresql://configured")
    monkeypatch.setattr(analytics, "psycopg", object())
    monkeypatch.setattr(analytics, "_connect", lambda: connection)

    analytics.record_event(" Student@Example.com ", None, "/chat/session-123")

    assert connection.params[0] == analytics._user_key("student@example.com")
    assert connection.params[1] == "unknown"
    assert connection.params[2] == "/chat"


def test_record_event_skips_empty_identity(monkeypatch):
    monkeypatch.setattr(analytics, "DATABASE_URL", "postgresql://configured")
    monkeypatch.setattr(analytics, "psycopg", object())
    monkeypatch.setattr(
        analytics,
        "_connect",
        lambda: (_ for _ in ()).throw(AssertionError("must not connect")),
    )

    analytics.record_event("   ", "chat", "/chat")
