from backend.memory_system.conversation_manager import ConversationManager


def test_conversation_manager_returns_detached_conversation_snapshots(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    manager = ConversationManager()
    conversation_id = manager.create("student@example.com")
    assert manager.add_message("student@example.com", conversation_id, "user", "Algebra")

    snapshot = manager.get("student@example.com", conversation_id)
    snapshot["messages"][0]["text"] = "Injected"
    listed = manager.list("student@example.com")
    listed[conversation_id]["title"] = "Injected"

    stored = manager.get("student@example.com", conversation_id)
    assert stored["messages"][0]["text"] == "Algebra"
    assert stored["title"] == "Algebra"


def test_conversation_manager_rejects_invalid_message_payloads(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    manager = ConversationManager()
    conversation_id = manager.create("student@example.com")

    assert manager.add_message("student@example.com", conversation_id, "attacker", "text") is False
    assert manager.add_message("student@example.com", conversation_id, "user", "   ") is False
    assert manager.add_message("student@example.com", conversation_id, "user", None) is False
    assert manager.get("student@example.com", conversation_id)["messages"] == []


def test_conversation_manager_rejects_oversized_manual_titles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    manager = ConversationManager()
    conversation_id = manager.create("student@example.com")

    assert manager.rename("student@example.com", conversation_id, "x" * 101) is False
    assert manager.rename("student@example.com", conversation_id, "Valid title") is True
