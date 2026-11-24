# Tests of the conversation endpoints in backend/app/protected.py, the rows
# in backend/app/conversations.py, and the answers for errors of the agent
# module in backend/app/agent_errors.py. They start the whole application
# with the real agent module. Only the tests that send a message need the
# stand-in for the model provider.
import logging
import re
import secrets
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import SavedUser, portal_of
from fastapi.testclient import TestClient
from model_stand_in import ModelStandIn

from app.agent import (
    Agent,
    AgentError,
    ConversationBusyError,
    HistoryMessage,
)
from app.database import connect
from app.main import app

# The form of the ids that the agent module makes.
CONVERSATION_ID_FORM = re.compile(r"[0-9a-f]{32}")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def start_conversation(client: TestClient, token: str) -> dict[str, Any]:
    response = client.post("/conversations", headers=bearer(token))
    assert response.status_code == 201, response.text
    conversation: dict[str, Any] = response.json()
    return conversation


def list_ids(client: TestClient, token: str) -> list[str]:
    response = client.get("/conversations", headers=bearer(token))
    assert response.status_code == 200, response.text
    return [entry["id"] for entry in response.json()["conversations"]]


def run_sql(database_file: Path, sql: str, parameters: tuple[Any, ...] = ()) -> None:
    connection = connect(database_file)
    with connection:
        connection.execute(sql, parameters)
    connection.close()


def the_agent() -> Agent:
    # The one agent object that the start-up of the application made.
    agent: Agent = app.state.agent
    return agent


class RecordedCalls:
    # Stands in for an action of the agent and records each call.
    def __init__(self) -> None:
        self.conversation_ids: list[str] = []

    async def read_history(self, conversation_id: str) -> list[HistoryMessage]:
        self.conversation_ids.append(conversation_id)
        return []


def raising(error: Exception) -> Callable[..., Any]:
    # Stands in for an action of the agent and raises the given error.
    async def action(*arguments: Any) -> Any:
        raise error

    return action


def test_the_list_holds_only_the_users_own_conversations(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    alice_token = sign_in(add_user("alice"))
    bob_token = sign_in(add_user("bob"))

    alice_ids = {start_conversation(client, alice_token)["id"] for _ in range(2)}
    bob_ids = {start_conversation(client, bob_token)["id"] for _ in range(3)}

    alice_list = list_ids(client, alice_token)
    bob_list = list_ids(client, bob_token)
    assert len(alice_list) == 2
    assert set(alice_list) == alice_ids
    assert len(bob_list) == 3
    assert set(bob_list) == bob_ids


def test_another_users_conversation_gets_the_same_answer_as_one_that_does_not_exist(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    alice_token = sign_in(add_user("alice"))
    bob_token = sign_in(add_user("bob"))
    bobs_id = start_conversation(client, bob_token)["id"]
    # Shows that the conversation exists and can be read by its owner.
    response = client.get(
        f"/conversations/{bobs_id}/messages", headers=bearer(bob_token)
    )
    assert response.status_code == 200

    answers = []
    for conversation_id in (
        bobs_id,
        secrets.token_hex(16),
        "not-a-conversation-id",
    ):
        response = client.get(
            f"/conversations/{conversation_id}/messages", headers=bearer(alice_token)
        )
        answers.append((response.status_code, response.json()))

    assert answers[0] == (404, {"detail": "Conversation not found"})
    assert answers[1] == answers[0]
    assert answers[2] == answers[0]


def test_a_request_that_gets_404_does_not_reach_the_agent(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alice_token = sign_in(add_user("alice"))
    bob_token = sign_in(add_user("bob"))
    bobs_id = start_conversation(client, bob_token)["id"]
    recorded = RecordedCalls()
    monkeypatch.setattr(the_agent(), "read_history", recorded.read_history)

    for conversation_id in (bobs_id, secrets.token_hex(16), "not-a-conversation-id"):
        response = client.get(
            f"/conversations/{conversation_id}/messages", headers=bearer(alice_token)
        )
        assert response.status_code == 404

    assert recorded.conversation_ids == []
    # Shows that the stand-in is called when the conversation is found.
    response = client.get(
        f"/conversations/{bobs_id}/messages", headers=bearer(bob_token)
    )
    assert response.status_code == 200
    assert recorded.conversation_ids == [bobs_id]


def test_the_list_gives_the_title_and_null_for_no_title(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
) -> None:
    token = sign_in(add_user("alice"))
    with_title = start_conversation(client, token)["id"]
    without_title = start_conversation(client, token)["id"]
    # No endpoint writes a title yet, so the test writes one into the table.
    run_sql(
        database_file,
        "UPDATE conversations SET title = ? WHERE id = ?",
        ("Plans for the weekend", with_title),
    )

    response = client.get("/conversations", headers=bearer(token))

    titles = {entry["id"]: entry["title"] for entry in response.json()["conversations"]}
    assert titles == {with_title: "Plans for the weekend", without_title: None}


def test_starting_a_conversation_stores_its_row_and_makes_its_session(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
) -> None:
    alice = add_user("alice")
    token = sign_in(alice)

    response = client.post("/conversations", headers=bearer(token))

    assert response.status_code == 201
    conversation = response.json()
    assert set(conversation) == {"id", "title", "created_at", "last_active_at"}
    assert CONVERSATION_ID_FORM.fullmatch(conversation["id"])
    assert conversation["title"] is None
    assert conversation["created_at"] == conversation["last_active_at"]

    connection = connect(database_file)
    rows = connection.execute(
        "SELECT id, user_id, created_at, last_active_at FROM conversations"
    ).fetchall()
    connection.close()
    assert len(rows) == 1
    assert rows[0]["id"] == conversation["id"]
    assert rows[0]["user_id"] == alice.id
    assert rows[0]["created_at"] == rows[0]["last_active_at"]
    # The stored form: UTC with milliseconds.
    assert re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z", rows[0]["created_at"]
    )

    # An empty history, and not an error, shows that the session exists.
    history = client.get(
        f"/conversations/{conversation['id']}/messages", headers=bearer(token)
    )
    assert history.status_code == 200
    assert history.json() == {"messages": []}


@pytest.mark.usefixtures("model_key")
def test_the_history_gives_the_messages_in_order(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    stand_in.answer("Blue ", "and white.")
    stand_in.answer("Green", ".")

    async def send(text: str) -> list[str]:
        # No endpoint sends a message yet, so the test sends through the agent
        # object of the application.
        answer = await the_agent().begin_answer(conversation_id, text)
        return [piece async for piece in answer]

    assert portal_of(client).call(send, "What colour is the sky?") == [
        "Blue ",
        "and white.",
    ]
    assert portal_of(client).call(send, "And the grass?") == ["Green", "."]

    response = client.get(
        f"/conversations/{conversation_id}/messages", headers=bearer(token)
    )

    assert response.status_code == 200
    assert response.json() == {
        "messages": [
            {"role": "user", "text": "What colour is the sky?"},
            {"role": "assistant", "text": "Blue and white."},
            {"role": "user", "text": "And the grass?"},
            {"role": "assistant", "text": "Green."},
        ]
    }


def test_the_list_is_ordered_by_the_last_activity_latest_first(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
) -> None:
    token = sign_in(add_user("alice"))
    first, second, third, fourth = (
        start_conversation(client, token)["id"] for _ in range(4)
    )
    # The times differ from the order of creation. The third and the fourth
    # have the same time, so the one made later must come first.
    times = {
        first: "2026-01-03T10:00:00.000Z",
        second: "2026-01-01T10:00:00.000Z",
        third: "2026-01-02T10:00:00.000Z",
        fourth: "2026-01-02T10:00:00.000Z",
    }
    for conversation_id, last_active_at in times.items():
        run_sql(
            database_file,
            "UPDATE conversations SET last_active_at = ? WHERE id = ?",
            (last_active_at, conversation_id),
        )

    assert list_ids(client, token) == [first, fourth, third, second]


def test_a_busy_conversation_gets_409(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    error_text = secrets.token_hex(8)
    monkeypatch.setattr(
        the_agent(), "read_history", raising(ConversationBusyError(error_text))
    )

    response = client.get(
        f"/conversations/{conversation_id}/messages", headers=bearer(token)
    )

    assert response.status_code == 409
    assert set(response.json()) == {"detail"}
    assert error_text not in response.text


@pytest.mark.parametrize("action", ["read_history", "start_conversation"])
def test_another_agent_error_gets_500_and_goes_to_the_log(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    action: str,
) -> None:
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    error_text = secrets.token_hex(8)
    monkeypatch.setattr(the_agent(), action, raising(AgentError(error_text)))

    if action == "read_history":
        response = client.get(
            f"/conversations/{conversation_id}/messages", headers=bearer(token)
        )
    else:
        response = client.post("/conversations", headers=bearer(token))

    assert response.status_code == 500
    assert set(response.json()) == {"detail"}
    assert error_text not in response.text
    assert any(
        record.levelno == logging.ERROR and error_text in record.getMessage()
        for record in caplog.records
    )


def test_a_row_whose_session_files_are_gone_gets_500(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
) -> None:
    alice = add_user("alice")
    token = sign_in(alice)
    # A row with no session files: the real agent finds no session for it.
    conversation_id = secrets.token_hex(16)
    run_sql(
        database_file,
        "INSERT INTO conversations (id, user_id) VALUES (?, ?)",
        (conversation_id, alice.id),
    )

    response = client.get(
        f"/conversations/{conversation_id}/messages", headers=bearer(token)
    )

    assert response.status_code == 500
    assert set(response.json()) == {"detail"}


def test_a_row_that_cannot_be_stored_gets_500_and_no_conversation(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
    session_directory: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = sign_in(add_user("alice"))
    # A trigger makes SQLite refuse every new row of conversations, so the
    # real insert fails after the agent has made the session.
    run_sql(
        database_file,
        "CREATE TRIGGER refuse_conversations BEFORE INSERT ON conversations "
        "BEGIN SELECT RAISE(ABORT, 'refused by the test'); END",
    )

    response = client.post("/conversations", headers=bearer(token))

    assert response.status_code == 500
    assert set(response.json()) == {"detail"}
    assert "refused by the test" not in response.text
    assert list_ids(client, token) == []
    # The session stays on disk, and the log names it.
    error_lines = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.ERROR
    ]
    session_ids = [
        folder.name
        for folder in (session_directory / "session-state").iterdir()
        if CONVERSATION_ID_FORM.fullmatch(folder.name)
    ]
    assert len(session_ids) == 1
    assert any(session_ids[0] in line for line in error_lines)
