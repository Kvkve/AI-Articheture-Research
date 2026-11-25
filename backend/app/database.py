import sqlite3
from pathlib import Path

# conversations.id is text, not a number, because it is the same value as the
# session id that the agent module makes.
# conversations.title stays empty until the first message of the
# conversation, which sets it.
# Every time is in UTC. The two times of a conversation also keep
# milliseconds, because the list of conversations is ordered by
# last_active_at, and whole seconds would often be equal.
# conversations.last_active_at is the time of the last activity. A new
# conversation has the same value in both of its times, because SQLite gives
# 'now' one value for the whole of one statement.
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS conversations (
    id             TEXT PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id),
    title          TEXT,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_active_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""


def connect(database_file: Path, check_same_thread: bool = True) -> sqlite3.Connection:
    database_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_file, check_same_thread=check_same_thread)
    # SQLite does not check foreign keys unless each connection asks for it.
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def create_tables(connection: sqlite3.Connection) -> None:
    # executescript commits by itself before it runs.
    connection.executescript(SCHEMA)
