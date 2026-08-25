import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.memory_system.conversation_manager import ConversationManager


class ConversationManagerTests(unittest.TestCase):
    def test_uses_configured_conversation_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "conversations.json"
            with patch.dict("os.environ", {"NOVA_CONVERSATIONS_FILE": str(path)}, clear=False):
                manager = ConversationManager()
                conversation_id = manager.create("student@example.com")
                manager.add_message("student@example.com", conversation_id, "user", "Hello Nova")

                reopened = ConversationManager()
                conversation = reopened.get("student@example.com", conversation_id)

            self.assertIsNotNone(conversation)
            self.assertEqual(conversation["title"], "Hello Nova")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["users"]["student@example.com"]["conversations"][conversation_id]["messages"][0]["text"], "Hello Nova")

    def test_stale_manager_does_not_overwrite_new_conversation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "conversations.json"
            with patch.dict("os.environ", {"NOVA_CONVERSATIONS_FILE": str(path)}, clear=False):
                first = ConversationManager()
                second = ConversationManager()
                first_id = first.create("student@example.com")
                second_id = second.create("student@example.com")
                conversations = ConversationManager().list("student@example.com")

            self.assertIn(first_id, conversations)
            self.assertIn(second_id, conversations)


if __name__ == "__main__":
    unittest.main()
