import hashlib
import json

from backend.memory_system.learning_memory import LearningMemory
from backend.user_context import user_context


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



def test_learning_memory_normalizes_existing_concept_attempts_and_confidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with user_context("concepts@example.com"):
        memory = LearningMemory()
        memory.data["concepts"]["Mathematics::Algebra"] = {
            "subject": "Mathematics",
            "concept": "Algebra",
            "confidence": float("inf"),
            "attempts": "broken",
        }
        memory.save()
        restored = LearningMemory()
        restored.update_concept("Mathematics", "Algebra", 90)

    concept = restored.get_concept("Mathematics", "Algebra")
    assert concept["confidence"] == 90
    assert concept["attempts"] == 1
    assert concept["first_seen"] is None



def test_learning_memory_uses_distinct_files_for_each_active_student(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with user_context("Student.One@example.com"):
        first = LearningMemory()
    with user_context("student.two@example.com"):
        second = LearningMemory()

    assert first.file != second.file
    assert first.file.name == hashlib.sha256(b"student.one@example.com").hexdigest() + ".json"
    assert second.file.name == hashlib.sha256(b"student.two@example.com").hexdigest() + ".json"


def test_learning_memory_normalizes_active_user_email(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with user_context("  Student@example.com  "):
        first = LearningMemory()
    with user_context("student@example.com"):
        second = LearningMemory()

    assert first.file == second.file
