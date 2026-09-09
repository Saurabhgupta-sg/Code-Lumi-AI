import tempfile
import unittest
from pathlib import Path

from code_lumi.auth.database import UserDatabase


class UserDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "test.db"
        self.database = UserDatabase(database_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_signup_and_login(self):
        created_user, message = self.database.create_user(
            "lumi_user",
            "lumi@example.com",
            "StrongPass1",
        )
        self.assertIsNotNone(created_user, message)

        signed_in_user, message = self.database.authenticate(
            "lumi@example.com",
            "StrongPass1",
        )
        self.assertIsNotNone(signed_in_user, message)
        self.assertEqual(signed_in_user.username, "lumi_user")

    def test_duplicate_account_is_rejected(self):
        self.database.create_user("lumi_user", "lumi@example.com", "StrongPass1")
        duplicate, _ = self.database.create_user(
            "LUMI_USER",
            "another@example.com",
            "StrongPass1",
        )
        self.assertIsNone(duplicate)

    def test_wrong_password_is_rejected(self):
        self.database.create_user("lumi_user", "lumi@example.com", "StrongPass1")
        user, _ = self.database.authenticate("lumi_user", "WrongPass1")
        self.assertIsNone(user)


if __name__ == "__main__":
    unittest.main()
