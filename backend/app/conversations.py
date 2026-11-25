import sqlite3
from datetime import datetime

from pydantic import BaseModel


class Conversation(BaseModel):
    # The id is also the id of the conversation's session in the agent module.
    id: str
    # None until the first message of the conversation; a later task fills it.
    title: str | None
    # The table stores these as text in UTC. Typed as datetime, the generated
    # API documentation marks them as date-time.
    created_at: datetime
    last_active_at: datetime


def _conversation_from(row: sqlite3.Row) -> Conversation:
    return Conversation(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        last_active_at=row["last_active_at"],
    )


def create_conversation(
    connection: sqlite3.Connection, conversation_id: str, user_id: int
) -> Conversation:
    # The two times come from the defaults of the table.
    # "with connection" commits when the block ends without an error, and
    # rolls back when it ends with one.
    with connection:
        row = connection.execute(
            "INSERT INTO conversations (id, user_id) VALUES (?, ?) "
            "RETURNING id, title, created_at, last_active_at",
            (conversation_id, user_id),
        ).fetchone()
    return _conversation_from(row)


def list_conversations(
    connection: sqlite3.Connection, user_id: int
) -> list[Conversation]:
    # rowid is the number SQLite gives each row as it is inserted, so a row
    # made later has a larger one. It breaks a tie of two equal times, which
    # created_at could not do for two rows made in the same millisecond.
    rows = connection.execute(
        "SELECT id, title, created_at, last_active_at FROM conversations "
        "WHERE user_id = ? "
        "ORDER BY last_active_at DESC, rowid DESC",
        (user_id,),
    ).fetchall()
    return [_conversation_from(row) for row in rows]


def find_conversation(
    connection: sqlite3.Connection, conversation_id: str, user_id: int
) -> Conversation | None:
    # One query with both conditions. A conversation of another user and an
    # id that no conversation has both give no row, so the caller cannot tell
    # them apart.
    row = connection.execute(
        "SELECT id, title, created_at, last_active_at FROM conversations "
        "WHERE id = ? AND user_id = ?",
        (conversation_id, user_id),
    ).fetchone()
    if row is None:
        return None
    return _conversation_from(row)
