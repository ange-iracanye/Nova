import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import auth


class AuthSecurityTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.users_file = Path(self.temp_dir.name) / "users.json"
        self.patch_users_file = patch.object(auth, "USERS_FILE", self.users_file)
        self.patch_users_file.start()

    def tearDown(self):
        self.patch_users_file.stop()
        self.temp_dir.cleanup()

    def test_password_hash_is_salted_and_not_plaintext(self):
        password = "Nova-test-password-123!"
        first = auth.hash_password(password)
        second = auth.hash_password(password)

        self.assertNotEqual(first, password)
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("scrypt$"))
        self.assertTrue(auth.verify_password(password, first))
        self.assertFalse(auth.verify_password("wrong-password", first))

    def test_register_and_login_store_scrypt_hash(self):
        self.assertTrue(auth.register_user("Student@Example.com", "Strong-password-1"))
        self.assertFalse(auth.register_user("student@example.com", "Another-password"))

        data = json.loads(self.users_file.read_text(encoding="utf-8"))
        stored = data["users"]["student@example.com"]["password"]

        self.assertTrue(stored.startswith("scrypt$"))
        self.assertTrue(auth.login_user("STUDENT@example.com", "Strong-password-1"))
        self.assertFalse(auth.login_user("student@example.com", "wrong"))

    def test_legacy_sha256_hash_is_migrated_after_login(self):
        password = "legacy-password"
        legacy_hash = auth.hashlib.sha256(password.encode("utf-8")).hexdigest()

        auth.save_users(
            {
                "users": {
                    "legacy@example.com": {
                        "email": "legacy@example.com",
                        "password": legacy_hash,
                    }
                }
            }
        )

        self.assertTrue(auth.login_user("legacy@example.com", password))

        data = json.loads(self.users_file.read_text(encoding="utf-8"))
        migrated = data["users"]["legacy@example.com"]["password"]
        self.assertTrue(migrated.startswith("scrypt$"))
        self.assertTrue(auth.verify_password(password, migrated))

    def test_corrupt_database_fails_closed(self):
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self.users_file.write_text("not-json", encoding="utf-8")

        with self.assertRaises(RuntimeError):
            auth.load_users()


if __name__ == "__main__":
    unittest.main()
