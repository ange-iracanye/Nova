from backend.learning_graph import LearningGraph
from backend.memory_system.memory_manager import MemoryManager


def test_learning_graph_storage_isolated_between_students(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    first = LearningGraph("first-student@example.com")
    second = LearningGraph("second-student@example.com")

    first.update_topic("Mathematics", "Algebra", True)

    assert first.get()["subjects"]["Mathematics"]["topics"]["Algebra"]["mastery"] == 100
    assert second.get()["subjects"] == {}
    assert first._user_path() != second._user_path()


def test_semantic_memory_storage_isolated_between_students(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_ENABLE_SEMANTIC_MEMORY", "false")
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", str(tmp_path / "conversations.json"))
    manager = MemoryManager(base_path=tmp_path / "memory")

    manager.add_memory("first-student@example.com", "Algebra revision")

    first = manager.load("first-student@example.com")
    second = manager.load("second-student@example.com")

    assert len(first["memories"]) == 1
    assert second["memories"] == []
    assert manager.user_file("first-student@example.com") != manager.user_file(
        "second-student@example.com"
    )
