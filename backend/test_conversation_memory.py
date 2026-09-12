import os
from pathlib import Path

from backend.memory_system.memory_manager import MemoryManager


def test_memory_reads_current_and_historical_conversations(tmp_path, monkeypatch):
    conversation_file = tmp_path / "conversations.json"
    memory_dir = tmp_path / "memory"
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", str(conversation_file))
    monkeypatch.setenv("NOVA_ENABLE_SEMANTIC_MEMORY", "false")

    manager = MemoryManager(base_path=str(memory_dir))
    email = "student@example.com"

    old_id = manager.conversations.create(email)
    manager.conversations.add_message(email, old_id, "user", "We studied quadratic equations and factoring.")
    manager.conversations.add_message(email, old_id, "nova", "Factoring helps solve many quadratic equations.")

    current_id = manager.conversations.create(email)
    manager.conversations.add_message(email, current_id, "user", "We are working on algebra today.")
    manager.conversations.add_message(email, current_id, "nova", "Sure, let's work through the algebra step by step.")
    manager.conversations.add_message(email, current_id, "user", "What did we say about factoring earlier?")

    context = manager.build_context(email, "factoring", limit=4)

    assert "CURRENT CONVERSATION" in context
    assert "What did we say about factoring earlier?" in context
    assert "RELEVANT PREVIOUS CONVERSATION" in context
    assert "quadratic equations" in context


def test_deleted_conversation_is_not_retrieved(tmp_path, monkeypatch):
    conversation_file = tmp_path / "conversations.json"
    memory_dir = tmp_path / "memory"
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", str(conversation_file))
    monkeypatch.setenv("NOVA_ENABLE_SEMANTIC_MEMORY", "false")

    manager = MemoryManager(base_path=str(memory_dir))
    email = "student@example.com"
    cid = manager.conversations.create(email)
    manager.conversations.add_message(email, cid, "user", "Remember this secret project phrase.")
    manager.conversations.add_message(email, cid, "nova", "Stored in the conversation.")
    manager.conversations.delete(email, cid)

    context = manager.build_context(email, "secret project phrase", limit=4)
    assert "secret project phrase" not in context
