import hashlib

from backend.memory_system.learning_memory import LearningMemory
from backend.user_context import user_context


def test_learning_memory_uses_distinct_files_for_each_active_student(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with user_context("Student.One@example.com"):
        first = LearningMemory()
    with user_context("student.two@example.com"):
        second = LearningMemory()

    assert first.file != second.file
    assert first.file.name == hashlib.sha256(
        b"student.one@example.com"
    ).hexdigest() + ".json"
    assert second.file.name == hashlib.sha256(
        b"student.two@example.com"
    ).hexdigest() + ".json"


def test_learning_memory_normalizes_active_user_email(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with user_context("  Student@example.com  "):
        first = LearningMemory()
    with user_context("student@example.com"):
        second = LearningMemory()

    assert first.file == second.file


def test_learning_memory_keeps_anonymous_legacy_store_separate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with user_context(None):
        memory = LearningMemory()

    assert memory.file.as_posix().endswith("data/memory/learning_memory.json")
