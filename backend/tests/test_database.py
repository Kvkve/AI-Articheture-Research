import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import connect, create_tables
from app.main import app


def column_names(connection: sqlite3.Connection, table: str) -> list[str]:
    # PRAGMA cannot take a ? placeholder; the table names here are fixed.
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return [row["name"] for row in rows]


def test_first_start_makes_the_file_and_the_tables(database_file: Path) -> None:
    assert not database_file.exists()

    # Entering the "with" block runs the application's start-up.
    with TestClient(app):
        pass

    assert database_file.exists()
    connection = connect(database_file)
    assert column_names(connection, "users") == [
        "id",
        "username",
        "password_hash",
        "created_at",
    ]
    assert column_names(connection, "conversations") == [
        "id",
        "user_id",
        "title",
        "created_at",
    ]
    connection.close()


def test_a_later_start_keeps_the_data(database_file: Path) -> None:
    with TestClient(app):
        pass
    connection = connect(database_file)
    with connection:
        connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("alice", "not-a-real-hash"),
        )
    connection.close()

    with TestClient(app):
        pass

    connection = connect(database_file)
    rows = connection.execute("SELECT username FROM users").fetchall()
    connection.close()
    assert [row["username"] for row in rows] == ["alice"]


def test_a_conversation_needs_an_existing_user(database_file: Path) -> None:
    connection = connect(database_file)
    create_tables(connection)

    with pytest.raises(sqlite3.IntegrityError), connection:
        connection.execute(
            "INSERT INTO conversations (id, user_id) VALUES (?, ?)",
            (str(uuid.uuid4()), 12345),
        )

    count = connection.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    connection.close()
    assert count == 0
