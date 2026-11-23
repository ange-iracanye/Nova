import json

from backend.memory_system.conversation_manager import ConversationManager


def test_conversation_manager_recovers_from_invalid_utf8(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    path = tmp_path / "data" / "conversations.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xff\xfe")

    manager = ConversationManager()
    conversation_id = manager.create("student@example.com")

    assert manager.get("student@example.com", conversation_id)["messages"] == []


def test_conversation_manager_repairs_malformed_message_collection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    manager = ConversationManager()
    conversation_id = manager.create("student@example.com")
    user = manager.data["users"]["student@example.com"]
    user["conversations"][conversation_id]["messages"] = "broken"

    assert manager.add_message("student@example.com", conversation_id, "user", "Hello Nova")
    conversation = manager.get("student@example.com", conversation_id)
    assert len(conversation["messages"]) == 1
    assert conversation["messages"][0]["text"] == "Hello Nova"


def test_conversation_title_normalizes_non_string_input(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    manager = ConversationManager()

    assert manager.generate_title(None) == "New Chat"
    assert manager.generate_title(123) == "123"



def test_conversation_manager_normalizes_malformed_persisted_users_and_messages(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    path = tmp_path / "data" / "conversations.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "users": {
            "STUDENT@example.com": {
                "conversations": {
                    "valid-id": {
                        "title": "   ",
                        "messages": [None, "broken", {"role": "user", "text": "Algebra"}],
                    },
                    "invalid-id": "not-a-conversation",
                }
            },
            "broken@example.com": "not-a-user",
        }
    }), encoding="utf-8")

    manager = ConversationManager()
    conversation = manager.get("student@example.com", "valid-id")

    assert conversation["title"] == "New Chat"
    assert conversation["messages"] == [{"role": "user", "text": "Algebra"}]
    assert manager.get("student@example.com", "invalid-id") is None
    assert manager.list("broken@example.com") == {}
