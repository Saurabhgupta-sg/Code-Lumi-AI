"""SQLite-backed user authentication for Code Lumi AI.

Passwords are never stored directly. Each password is hashed with PBKDF2-HMAC
and a unique cryptographically secure salt before it reaches the database.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = APP_DIR / "data" / "code_lumi.db"
SCHEMA_PATH = APP_DIR / "schema.sql"
PASSWORD_ITERATIONS = 600_000

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class AuthenticatedUser:
    """The non-sensitive account fields exposed to the desktop UI."""

    id: int
    username: str
    email: str
    role: str


@dataclass(frozen=True)
class UserRecord:
    """Account information displayed in the administrator user list."""

    id: int
    username: str
    email: str
    role: str
    created_at: str
    last_login_at: str | None


class UserDatabase:
    """Small repository class that owns all user-related SQL operations."""

    def __init__(self, database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        with self._connect() as connection:
            connection.executescript(schema)
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
            if "role" not in columns:
                connection.execute(
                    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
                )

            # Existing installations did not have roles. Promote the earliest
            # account once so the owner can administer the database using the
            # password they already have.
            admin_count = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin'"
            ).fetchone()[0]
            if admin_count == 0:
                first_user = connection.execute(
                    "SELECT id FROM users ORDER BY id LIMIT 1"
                ).fetchone()
                if first_user is not None:
                    connection.execute(
                        "UPDATE users SET role = 'admin' WHERE id = ?",
                        (first_user["id"],),
                    )

    @staticmethod
    def _hash_password(
        password: str,
        salt: bytes | None = None,
        iterations: int = PASSWORD_ITERATIONS,
    ) -> tuple[str, str]:
        actual_salt = salt or secrets.token_bytes(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            actual_salt,
            iterations,
        )
        return (
            base64.b64encode(password_hash).decode("ascii"),
            base64.b64encode(actual_salt).decode("ascii"),
        )

    @staticmethod
    def _validate_signup(username: str, email: str, password: str) -> str | None:
        if not USERNAME_PATTERN.fullmatch(username):
            return "Username must be 3-30 characters and use only letters, numbers, ., _ or -."
        if not EMAIL_PATTERN.fullmatch(email):
            return "Enter a valid email address."
        password_error = UserDatabase._validate_password(password)
        if password_error:
            return password_error
        return None

    @staticmethod
    def _validate_password(password: str) -> str | None:
        if len(password) < 8:
            return "Password must contain at least 8 characters."
        if not any(character.isupper() for character in password):
            return "Password must contain an uppercase letter."
        if not any(character.islower() for character in password):
            return "Password must contain a lowercase letter."
        if not any(character.isdigit() for character in password):
            return "Password must contain a number."
        return None

    @staticmethod
    def _is_admin(connection: sqlite3.Connection, user_id: int) -> bool:
        row = connection.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return row is not None and row["role"] == "admin"

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
    ) -> tuple[AuthenticatedUser | None, str]:
        normalized_username = username.strip()
        normalized_email = email.strip().lower()
        validation_error = self._validate_signup(
            normalized_username,
            normalized_email,
            password,
        )
        if validation_error:
            return None, validation_error

        password_hash, password_salt = self._hash_password(password)
        try:
            with self._connect() as connection:
                is_first_account = connection.execute(
                    "SELECT COUNT(*) FROM users"
                ).fetchone()[0] == 0
                role = "admin" if is_first_account else "user"
                cursor = connection.execute(
                    """
                    INSERT INTO users (
                        username,
                        email,
                        password_hash,
                        password_salt,
                        password_iterations,
                        role
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_username,
                        normalized_email,
                        password_hash,
                        password_salt,
                        PASSWORD_ITERATIONS,
                        role,
                    ),
                )
                user_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError:
            return None, "That username or email is already registered."

        return (
            AuthenticatedUser(user_id, normalized_username, normalized_email, role),
            "Account created successfully.",
        )

    def authenticate(
        self,
        username_or_email: str,
        password: str,
    ) -> tuple[AuthenticatedUser | None, str]:
        identifier = username_or_email.strip()
        if not identifier or not password:
            return None, "Enter your username/email and password."

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    password_hash,
                    password_salt,
                    password_iterations,
                    role
                FROM users
                WHERE username = ? COLLATE NOCASE
                   OR email = ? COLLATE NOCASE
                LIMIT 1
                """,
                (identifier, identifier),
            ).fetchone()

            if row is None:
                return None, "Incorrect username/email or password."

            salt = base64.b64decode(row["password_salt"])
            calculated_hash, _ = self._hash_password(
                password,
                salt=salt,
                iterations=int(row["password_iterations"]),
            )
            if not hmac.compare_digest(calculated_hash, row["password_hash"]):
                return None, "Incorrect username/email or password."

            connection.execute(
                "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
                (row["id"],),
            )

        return (
            AuthenticatedUser(
                int(row["id"]),
                row["username"],
                row["email"],
                row["role"],
            ),
            "Login successful.",
        )

    def list_users(
        self,
        admin_user_id: int,
    ) -> tuple[list[UserRecord], str]:
        """Return every account when the requester is an administrator."""
        with self._connect() as connection:
            if not self._is_admin(connection, admin_user_id):
                return [], "Administrator access is required."
            rows = connection.execute(
                """
                SELECT id, username, email, role, created_at, last_login_at
                FROM users
                ORDER BY CASE role WHEN 'admin' THEN 0 ELSE 1 END, username
                """
            ).fetchall()

        return (
            [
                UserRecord(
                    id=int(row["id"]),
                    username=row["username"],
                    email=row["email"],
                    role=row["role"],
                    created_at=row["created_at"],
                    last_login_at=row["last_login_at"],
                )
                for row in rows
            ],
            "Users loaded.",
        )

    def create_user_as_admin(
        self,
        admin_user_id: int,
        username: str,
        email: str,
        password: str,
        role: str = "user",
    ) -> tuple[AuthenticatedUser | None, str]:
        normalized_username = username.strip()
        normalized_email = email.strip().lower()
        normalized_role = role.strip().lower()
        validation_error = self._validate_signup(
            normalized_username,
            normalized_email,
            password,
        )
        if validation_error:
            return None, validation_error
        if normalized_role not in {"user", "admin"}:
            return None, "Role must be user or admin."

        password_hash, password_salt = self._hash_password(password)
        try:
            with self._connect() as connection:
                if not self._is_admin(connection, admin_user_id):
                    return None, "Administrator access is required."
                cursor = connection.execute(
                    """
                    INSERT INTO users (
                        username,
                        email,
                        password_hash,
                        password_salt,
                        password_iterations,
                        role
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_username,
                        normalized_email,
                        password_hash,
                        password_salt,
                        PASSWORD_ITERATIONS,
                        normalized_role,
                    ),
                )
                new_user_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError:
            return None, "That username or email is already registered."

        return (
            AuthenticatedUser(
                new_user_id,
                normalized_username,
                normalized_email,
                normalized_role,
            ),
            "User added successfully.",
        )

    def change_password_as_admin(
        self,
        admin_user_id: int,
        target_user_id: int,
        new_password: str,
    ) -> tuple[bool, str]:
        password_error = self._validate_password(new_password)
        if password_error:
            return False, password_error

        password_hash, password_salt = self._hash_password(new_password)
        with self._connect() as connection:
            if not self._is_admin(connection, admin_user_id):
                return False, "Administrator access is required."
            cursor = connection.execute(
                """
                UPDATE users
                SET password_hash = ?,
                    password_salt = ?,
                    password_iterations = ?
                WHERE id = ?
                """,
                (
                    password_hash,
                    password_salt,
                    PASSWORD_ITERATIONS,
                    target_user_id,
                ),
            )
            if cursor.rowcount == 0:
                return False, "User was not found."
        return True, "Password changed successfully."

    def delete_user_as_admin(
        self,
        admin_user_id: int,
        target_user_id: int,
    ) -> tuple[bool, str]:
        if admin_user_id == target_user_id:
            return False, "You cannot delete the account currently signed in."

        with self._connect() as connection:
            if not self._is_admin(connection, admin_user_id):
                return False, "Administrator access is required."
            target = connection.execute(
                "SELECT role FROM users WHERE id = ?",
                (target_user_id,),
            ).fetchone()
            if target is None:
                return False, "User was not found."
            if target["role"] == "admin":
                admin_count = connection.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin'"
                ).fetchone()[0]
                if admin_count <= 1:
                    return False, "The last administrator cannot be deleted."
            connection.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
        return True, "User deleted successfully."