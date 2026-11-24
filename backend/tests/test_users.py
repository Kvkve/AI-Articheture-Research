import secrets
from pathlib import Path

import pytest

from app.database import connect, create_tables
from app.security import hash_password, verify_password
from app.users import InvalidUserError, create_user


def make_password() -> str:
    return secrets.token_urlsafe(16)


def test_create_user_stores_a_hash_not_the_password(database_file: Path) -> None:
    password = make_password()
    connection = connect(database_file)
    create_tables(connection)

    user_id = create_user(connection, "  alice  ", password)

    row = connection.execute(
        "SELECT username, password_hash FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    connection.close()
    assert row["username"] == "alice"
    assert row["password_hash"] != password
    # The other checks would also pass for a scheme that can be reversed, such
    # as encryption with a random start value. This prefix names Argon2, which
    # is one-way.
    assert row["password_hash"].startswith("$argon2id$")
    assert verify_password(password, row["password_hash"])
    assert password.encode() not in database_file.read_bytes()


def test_verify_password_refuses_a_wrong_password() -> None:
    password = make_password()
    stored = hash_password(password)

    assert verify_password(password, stored)
    assert not verify_password(make_password(), stored)


def test_the_same_password_hashes_to_different_values() -> None:
    password = make_password()

    assert hash_password(password) != hash_password(password)


@pytest.mark.parametrize("username", ["", "   "])
def test_create_user_refuses_an_empty_username(
    database_file: Path, username: str
) -> None:
    connection = connect(database_file)
    create_tables(connection)

    with pytest.raises(InvalidUserError):
        create_user(connection, username, make_password())

    count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    connection.close()
    assert count == 0


def test_create_user_refuses_an_empty_password(database_file: Path) -> None:
    connection = connect(database_file)
    create_tables(connection)

    with pytest.raises(InvalidUserError):
        create_user(connection, "alice", "")

    count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    connection.close()
    assert count == 0
