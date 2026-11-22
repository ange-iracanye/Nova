from backend.memory_system.memory_manager import MemoryManager


def test_conversation_text_ignores_malformed_conversation_payloads():
    assert MemoryManager._conversation_text(None) == ""
    assert MemoryManager._conversation_text("broken") == ""
    assert MemoryManager._conversation_text({"messages": "broken"}) == ""
    assert MemoryManager._conversation_text({
        "messages": [None, "broken", {"role": "user", "text": "Algebra"}]
    }) == "User: Algebra"


def test_conversation_context_returns_empty_for_only_malformed_records(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    manager = MemoryManager(base_path=tmp_path / "memory")
    manager.conversations.list = lambda email: {
        "broken": None,
        "also-broken": "not a conversation",
    }

    assert manager._conversation_context("student@example.com", "when did we talk?", 1000) == ""
