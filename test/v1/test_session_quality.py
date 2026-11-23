import json

from backend.learning import session_quality


class DummySessionManager:
    def __init__(self):
        self.session = {}


def _install(monkeypatch, tmp_path):
    path = tmp_path / "session.json"
    monkeypatch.setattr(session_quality, "_file", lambda: path)
    monkeypatch.setattr(session_quality, "_PATCHED", False)
    session_quality.install_session_quality(DummySessionManager)
    return path


def test_persistent_session_resets_state_when_started(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manager = DummySessionManager()
    manager.start("Mathematics", "Algebra", "practice")
    manager.ask("Solve x + 1 = 3")
    manager.add_score(5)

    result = manager.start("Physics", "Motion", "exam")

    assert result["subject"] == "Physics"
    assert result["score"] == 0
    assert result["questions"] == 0
    assert result["waiting_answer"] is False


def test_persistent_session_repairs_malformed_json_and_values(monkeypatch, tmp_path):
    path = _install(monkeypatch, tmp_path)
    path.write_text(json.dumps({
        "subject": ["bad"],
        "waiting_answer": "false",
        "score": float("inf"),
        "questions": "invalid",
        "last_question": 7,
    }), encoding="utf-8")

    manager = DummySessionManager()
    result = manager.get()

    assert result["subject"] is None
    assert result["waiting_answer"] is False
    assert result["score"] == 0
    assert result["questions"] == 0
    assert result["last_question"] is None


def test_persistent_session_rejects_invalid_scores_and_questions(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manager = DummySessionManager()
    manager.start("Biology", "Cells", "practice")

    assert manager.ask("  ") is False
    assert manager.add_score(float("nan")) == 0
    assert manager.add_score("invalid") == 0
    assert manager.get()["questions"] == 0


def test_persistent_session_get_returns_snapshot(monkeypatch, tmp_path):
    _install(monkeypatch, tmp_path)
    manager = DummySessionManager()
    manager.start("Biology", "Cells", "practice")

    snapshot = manager.get()
    snapshot["subject"] = "Injected"

    assert manager.get()["subject"] == "Biology"
