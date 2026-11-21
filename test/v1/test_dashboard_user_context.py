from backend import dashboard
from backend.user_context import get_active_user, set_active_user


def test_dashboard_restores_previous_user_after_success(monkeypatch):
    set_active_user("previous@example.com")

    def build(email):
        assert email == "student@example.com"
        assert get_active_user() == "student@example.com"
        return {"ok": True}

    monkeypatch.setattr(dashboard, "_build_dashboard_data", build)

    assert dashboard._build_dashboard("student@example.com") == {"ok": True}
    assert get_active_user() == "previous@example.com"


def test_dashboard_restores_user_context_after_failure(monkeypatch):
    set_active_user(None)

    def fail(_email):
        assert get_active_user() == "student@example.com"
        raise RuntimeError("dashboard source unavailable")

    monkeypatch.setattr(dashboard, "_build_dashboard_data", fail)

    try:
        dashboard._build_dashboard("student@example.com")
    except RuntimeError as error:
        assert str(error) == "dashboard source unavailable"
    else:
        raise AssertionError("Expected the dashboard build to fail")

    assert get_active_user() is None
