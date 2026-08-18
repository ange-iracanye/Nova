import tempfile
import unittest
from pathlib import Path

from backend.persistent_sessions import PersistentSessionStore


class PersistentSessionStoreTests(unittest.TestCase):
    def test_sessions_survive_a_new_store_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.sqlite3"
            session = {
                "token": "token-123",
                "email": "student@example.com",
                "expires_at": "2999-01-01T00:00:00+00:00",
            }

            first = PersistentSessionStore(str(path))
            first["token-123"] = session

            second = PersistentSessionStore(str(path))
            self.assertEqual(second["token-123"]["email"], "student@example.com")
            self.assertEqual(len(second), 1)

    def test_expired_sessions_are_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sessions.sqlite3"
            store = PersistentSessionStore(str(path))
            store["expired"] = {
                "token": "expired",
                "email": "student@example.com",
                "expires_at": "2000-01-01T00:00:00+00:00",
            }

            self.assertIsNone(store.get("expired"))
            self.assertEqual(len(store), 0)


if __name__ == "__main__":
    unittest.main()
