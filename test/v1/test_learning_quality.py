import json

from backend.memory_system import learning_quality
from backend.memory_system.learning_memory import LearningMemory
from backend.user_context import get_active_user, user_context


def _install(monkeypatch, tmp_path, email="learning-quality@example.com"):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(learning_quality, "get_active_user", lambda: email)
    monkeypatch.setattr(learning_quality, "set_active_user", lambda value: None)
    monkeypatch.setattr(learning_quality, "_PATCHED", False)
    learning_quality.install_learning_quality(type("MemoryManagerStub", (), {"remember": lambda *a, **k: None}), LearningMemory)
    return learning_quality._path(email)


def test_learning_quality_repairs_malformed_subject_counters(tmp_path, monkeypatch):
    path = _install(monkeypatch, tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "subjects": {
            "Mathematics": {
                "confidence": float("nan"),
                "attempts": "invalid",
                "correct": "2",
                "incorrect": float("inf"),
                "study_count": None,
            },
            "broken": "not-a-record",
        }
    }), encoding="utf-8")

    memory = LearningMemory()
    assert memory.record_attempt("Mathematics", float("inf"), correct=True) is True
    subject = memory.get_subject("Mathematics")

    assert subject["confidence"] == 50
    assert subject["attempts"] == 1
    assert subject["correct"] == 3
    assert subject["incorrect"] == 0
    assert subject["study_count"] == 1


def test_learning_quality_normalizes_concepts_and_returns_detached_records(tmp_path, monkeypatch):
    _install(monkeypatch, tmp_path, "concept-quality@example.com")
    memory = LearningMemory()

    assert memory.update_concept("Physics", "Motion", float("nan"), difficulty="medium")
    concept = memory.get_concept("Physics", "Motion")
    assert concept["confidence"] == 50
    concept["confidence"] = 0

    assert memory.get_concept("Physics", "Motion")["confidence"] == 50


def test_learning_quality_persists_strict_json_and_bounds_history(tmp_path, monkeypatch):
    path = _install(monkeypatch, tmp_path, "strict-learning@example.com")
    data = learning_quality._load("strict-learning@example.com")
    data["mistakes"] = [
        {"subject": "Math", "concept": "Algebra", "description": str(index)}
        for index in range(510)
    ]
    learning_quality._save("strict-learning@example.com", data)
    memory = LearningMemory()
    memory.record_mistake("Math", "Algebra", "latest")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert len(saved["mistakes"]) == 500



def test_learning_memory_storage_isolated_between_active_students(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    active = {"email": "first@example.com"}
    monkeypatch.setattr(
        learning_quality,
        "get_active_user",
        lambda: active["email"],
    )
    monkeypatch.setattr(
        learning_quality,
        "set_active_user",
        lambda email: active.update(email=email),
    )
    monkeypatch.setattr(learning_quality, "_PATCHED", False)
    learning_quality.install_learning_quality(
        type("MemoryManagerStub", (), {"remember": lambda *a, **k: None}),
        LearningMemory,
    )
    memory = LearningMemory()

    memory.record_attempt("Mathematics", 80, correct=True)
    active["email"] = "second@example.com"

    assert memory.get()["subjects"] == {}
    memory.record_attempt("Physics", 70, correct=False)
    assert set(memory.get()["subjects"]) == {"Physics"}

    active["email"] = "first@example.com"
    assert set(memory.get()["subjects"]) == {"Mathematics"}



def test_learning_memory_remember_restores_previous_active_user_context(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(learning_quality, "_PATCHED", False)

    class MemoryManagerStub:
        def remember(self, email):
            return get_active_user()

    learning_quality.install_learning_quality(MemoryManagerStub, LearningMemory)
    manager = MemoryManagerStub()

    with user_context("previous@example.com"):
        observed = manager.remember("target@example.com")
        after = get_active_user()

    assert observed == "target@example.com"
    assert after == "previous@example.com"
