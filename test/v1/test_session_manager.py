import math

from backend.learning.session_manager import SessionManager


def test_start_resets_previous_session_state():
    manager = SessionManager()
    manager.start("Mathematics", "Algebra", "practice")
    manager.ask("Solve x + 2 = 5")
    manager.add_score(4)

    snapshot = manager.start("Physics", "Motion", "exam")

    assert snapshot == {
        "subject": "Physics",
        "topic": "Motion",
        "mode": "exam",
        "waiting_answer": False,
        "last_question": None,
        "score": 0.0,
        "questions": 0,
    }


def test_empty_question_does_not_open_answer_state():
    manager = SessionManager()

    assert manager.ask("   ") is False
    assert manager.waiting() is False
    assert manager.get()["questions"] == 0


def test_score_rejects_invalid_and_non_finite_values():
    manager = SessionManager()
    manager.add_score(2.5)
    manager.add_score("invalid")
    manager.add_score(float("nan"))
    manager.add_score(float("inf"))

    assert manager.get()["score"] == 2.5
    assert math.isfinite(manager.get()["score"])


def test_get_returns_independent_snapshot():
    manager = SessionManager()
    manager.start("Biology", "Cells", "revision")

    snapshot = manager.get()
    snapshot["subject"] = "Changed"
    snapshot["questions"] = 99

    assert manager.get()["subject"] == "Biology"
    assert manager.get()["questions"] == 0
