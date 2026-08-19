import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend import auth
from backend.dashboard import _merge_topic_stats
from backend.learning.progress_tracker import canonical_subject
from backend.persistent_sessions import PersistentSessionStore


class NovaV1ReleaseTests(unittest.TestCase):
    def test_auth_passwords_are_scrypt_and_throttled(self):
        with tempfile.TemporaryDirectory() as directory:
            users_file = Path(directory) / "users.json"
            with patch.object(auth, "USERS_FILE", users_file):
                password = "Strong-Nova-Password-1"
                self.assertTrue(auth.register_user("student@example.com", password))
                data = json.loads(users_file.read_text(encoding="utf-8"))
                self.assertTrue(data["users"]["student@example.com"]["password"].startswith("scrypt$"))
                self.assertTrue(auth.login_user("student@example.com", password))

    def test_session_store_persists_and_expires(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.sqlite3"
            future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            store = PersistentSessionStore(str(path))
            store["token"] = {"email": "student@example.com", "expires_at": future}
            reopened = PersistentSessionStore(str(path))
            self.assertEqual(reopened["token"]["email"], "student@example.com")

            expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            reopened["expired"] = {"email": "student@example.com", "expires_at": expired}
            self.assertIsNone(reopened.get("expired"))
            self.assertNotIn("expired", list(reopened))

            del reopened
            del store

    def test_dynamic_subjects(self):
        self.assertEqual(canonical_subject("python"), "Technology")
        self.assertEqual(canonical_subject("French"), "Languages")
        self.assertEqual(canonical_subject("economics"), "Economics")
        self.assertEqual(canonical_subject("quantum computing"), "Technology")
        self.assertEqual(canonical_subject("Astrophotography"), "Astrophotography")

    def test_dashboard_is_evidence_based(self):
        subjects, attempts, correct, wrong, topics = _merge_topic_stats(
            {"Technology": {"Python": {"attempts": 1, "confidence": 65, "mastered": False}}},
            {},
        )
        self.assertEqual(attempts, 1)
        self.assertEqual(correct, 0)
        self.assertEqual(wrong, 0)
        self.assertEqual(topics, 1)
        self.assertEqual(subjects["Technology"]["mastery"], 65)
        self.assertFalse(subjects["Technology"]["topics"][0]["mastered"])


if __name__ == "__main__":
    unittest.main()
