import secrets
import sqlite3

from pydantic import BaseModel

from app.security import hash_password, verify_password

# A SQLite INTEGER is a signed 64-bit number.
LARGEST_SQLITE_INTEGER = 2**63 - 1


class InvalidUserError(ValueError):
    pass


class UserExistsError(Exception):
    pass


class User(BaseModel):
    # Never holds the password hash, so the hash cannot reach an answer of the API.
    id: int
    username: str


# Checked against when the user name is unknown, so that the answer takes
# about as long as for a known name. Unlike the template, which writes a fixed
# hash into the code, this one is made at start-up by the project's own
# hasher, so its cost settings always match those of the real hashes.
DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


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


def authenticate(
    connection: sqlite3.Connection, username: str, password: str
) -> User | None:
    """Return the user if the name and the password match, otherwise None."""
    # The name is stored without the white space around it; see create_user.
    username = username.strip()
    row = connection.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return User(id=row["id"], username=row["username"])


def get_user_by_id(connection: sqlite3.Connection, user_id: int) -> User | None:
    # sqlite3 raises OverflowError for a number that does not fit in a SQLite
    # INTEGER. No such id can be in the table.
    if user_id > LARGEST_SQLITE_INTEGER:
        return None
    row = connection.execute(
        "SELECT id, username FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    return User(id=row["id"], username=row["username"])
