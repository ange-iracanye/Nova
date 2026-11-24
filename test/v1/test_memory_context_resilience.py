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


def test_conversation_context_sorts_malformed_timestamps_safely(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    manager = MemoryManager(base_path=tmp_path / "memory")
    manager.conversations.list = lambda email: {
        "missing-date": {
            "updated_at": None,
            "messages": [{"role": "user", "text": "We revised algebra."}],
        },
        "valid-date": {
            "updated_at": "2026-11-20T12:00:00+00:00",
            "messages": [{"role": "user", "text": "We revised geometry."}],
        },
        "invalid-date": {
            "updated_at": {"unexpected": "object"},
            "messages": [{"role": "user", "text": "We revised fractions."}],
        },
    }

    context = manager._conversation_context("student@example.com", "when did we talk?", 4000)

    assert "CURRENT CONVERSATION" in context
    assert "RELEVANT PREVIOUS CONVERSATION" in context
