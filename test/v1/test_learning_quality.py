import json

from backend.memory_system import learning_quality
from backend.memory_system.learning_memory import LearningMemory


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
    memory = LearningMemory()
    for index in range(510):
        memory.record_mistake("Math", "Algebra", f"mistake {index}")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert len(saved["mistakes"]) == 500
