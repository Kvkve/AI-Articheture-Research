import sqlite3

from app.security import hash_password


class InvalidUserError(ValueError):
    pass


class UserExistsError(Exception):
    pass


def create_user(connection: sqlite3.Connection, username: str, password: str) -> int:
    username = username.strip()
    if not username:
        raise InvalidUserError("The user name must not be empty.")
    if not password:
        raise InvalidUserError("The password must not be empty.")

    try:
        # "with connection" commits when the block ends without an error,
        # and rolls back when it ends with one.
        with connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hash_password(password)),
            )
    except sqlite3.IntegrityError as error:
        # The only constraint an insert with both values can break is the
        # UNIQUE rule on username.
        raise UserExistsError(f"The user {username!r} already exists.") from error

    user_id = cursor.lastrowid
    if user_id is None:
        raise RuntimeError("SQLite gave no id for the new user.")
    return user_id
