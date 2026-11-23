import json

from backend.memory_system.learning_memory import LearningMemory


def test_learning_memory_recovers_from_invalid_root_and_nested_records(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with user_context("repair@example.com"):
        memory = LearningMemory()
        memory.file.write_text(json.dumps({
            "subjects": "broken",
            "concepts": {"valid": {"confidence": 80}, "invalid": None},
            "mistakes": "not-a-list",
            "successful_strategies": [{"strategy": "examples"}],
        }), encoding="utf-8")
        repaired = LearningMemory()

    assert repaired.data["subjects"] == {}
    assert repaired.data["concepts"] == {"valid": {"confidence": 80}}
    assert repaired.data["mistakes"] == []
    assert repaired.data["successful_strategies"] == [{"strategy": "examples"}]


def test_learning_memory_sanitizes_non_finite_scores_and_counts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with user_context("scores@example.com"):
        memory = LearningMemory()
        memory.data["subjects"]["Math"] = {
            "confidence": float("nan"),
            "attempts": "invalid",
            "correct": float("inf"),
            "incorrect": 1,
            "study_count": "broken",
        }
        memory.record_attempt("Math", float("inf"), correct=True)

        saved = json.loads(memory.file.read_text(encoding="utf-8"))

    assert saved["subjects"]["Math"]["confidence"] == 50
    assert saved["subjects"]["Math"]["attempts"] == 1
    assert saved["subjects"]["Math"]["correct"] == 1
    assert saved["subjects"]["Math"]["study_count"] == 1


def test_learning_memory_get_returns_detached_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with user_context("snapshot@example.com"):
        memory = LearningMemory()
        snapshot = memory.get()
        snapshot["subjects"]["injected"] = {}

    assert "injected" not in memory.get()["subjects"]
