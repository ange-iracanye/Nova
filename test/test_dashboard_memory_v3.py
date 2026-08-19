from backend.learning.progress_tracker import ProgressTracker
from backend.learning_graph import LearningGraph
from backend.memory_system.memory_manager import MemoryManager


class FakeEmbedder:
    def encode(self, text, normalize_embeddings=True):
        value = sum(ord(ch) for ch in str(text)) % 997
        return [float(value), 1.0]


def test_progress_is_user_isolated_and_not_instantly_mastered(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    alice = ProgressTracker("alice@example.com")
    bob = ProgressTracker("bob@example.com")
    alice.update("Technology", "Python", 100)

    assert "Technology" in alice.get()
    assert "Technology" not in bob.get()
    assert alice.get()["Technology"]["Python"]["confidence"] < 100
    assert alice.get()["Technology"]["Python"]["mastered"] is False


def test_memory_is_user_isolated_and_replaces_stale_preference(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    manager = MemoryManager(
        embedder=FakeEmbedder(),
        base_path=str(tmp_path / "memory"),
    )

    manager.add_memory(
        "alice@example.com",
        "I prefer short explanations",
        memory_type="preference",
        importance=0.8,
        confidence=0.9,
    )
    manager.add_memory(
        "alice@example.com",
        "I prefer detailed explanations for difficult topics",
        memory_type="preference",
        importance=0.95,
        confidence=1.0,
    )

    alice = manager.get_all("alice@example.com")
    bob = manager.get_all("bob@example.com")

    assert alice["memories"]
    assert bob["memories"] == []
    assert any(
        "detailed explanations" in item["text"]
        for item in alice["memories"]
    )


def test_learning_graph_reads_user_progress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    tracker = ProgressTracker("student@example.com")
    tracker.update("Technology", "Python", 80)
    tracker.update("Physics", "Newton's laws", 60)

    graph = LearningGraph("student@example.com").get()

    assert set(graph["subjects"]) == {"Technology", "Physics"}
    assert graph["subjects"]["Technology"]["topics"]["Python"]["mastery"] < 100
    assert graph["subjects"]["Physics"]["topics"]["Newton's laws"]["mastery"] < 100
