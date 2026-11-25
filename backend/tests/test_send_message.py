# Tests of the endpoint that sends a message and streams the answer, in
# backend/app/protected.py, with the title and the time it writes in
# backend/app/conversations.py and its error answers in
# backend/app/agent_errors.py. Most tests run the whole application with the
# real agent module against the stand-in for the model provider.
import json
import logging
import re
import secrets
import sqlite3
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    STAND_IN_WAIT_SECONDS,
    SavedUser,
    bearer,
    portal_of,
    run_sql,
    start_conversation,
    the_agent,
    wait_until_free,
)
from fastapi.testclient import TestClient
from model_stand_in import ModelStandIn

from app.agent import AgentError, ConversationBusyError
from app.agent_errors import (
    ANSWER_FAILED_TEXT,
    BUSY_TEXT,
    FAILED_TEXT,
    NO_MODEL_KEY_TEXT,
)
from app.database import connect

# Small settings for the tests that need them, so a test can pass the limit
# with a short text.
SMALL_TITLE_CHARACTERS = 12
SMALL_LONGEST_MESSAGE_CHARACTERS = 30

END = {"type": "end"}
FAILED = {"type": "error", "message": ANSWER_FAILED_TEXT}


def text(piece: str) -> dict[str, str]:
    return {"type": "text", "text": piece}


def messages_address(conversation_id: str) -> str:
    return f"/conversations/{conversation_id}/messages"


def read_messages(lines: Iterable[str]) -> Iterator[dict[str, Any]]:
    # Reads the stream as a frontend would: each message is one "data:" line
    # with one JSON object, followed by an empty line. A line that begins
    # with a colon is a comment and is skipped. Any other line fails the
    # test, because the format allows nothing else.
    for line in lines:
        if line == "" or line.startswith(":"):
            continue
        assert line.startswith("data: "), f"not a line of the format: {line!r}"
        message: dict[str, Any] = json.loads(line.removeprefix("data: "))
        yield message


def send(
    client: TestClient, token: str, conversation_id: str, message_text: str
) -> list[dict[str, Any]]:
    # Sends a message, checks that the answer is a stream, and reads it to
    # its end.
    with client.stream(
        "POST",
        messages_address(conversation_id),
        json={"text": message_text},
        headers=bearer(token),
    ) as response:
        assert response.status_code == 200, response.read()
        assert response.headers["content-type"].startswith("text/event-stream")
        return list(read_messages(response.iter_lines()))


def conversation_rows(database_file: Path) -> list[dict[str, Any]]:
    connection = connect(database_file)
    rows = connection.execute(
        "SELECT id, user_id, title, created_at, last_active_at FROM conversations "
        "ORDER BY rowid"
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def conversation_row(database_file: Path, conversation_id: str) -> dict[str, Any]:
    return next(
        row for row in conversation_rows(database_file) if row["id"] == conversation_id
    )


def list_entries(client: TestClient, token: str) -> list[dict[str, Any]]:
    response = client.get("/conversations", headers=bearer(token))
    assert response.status_code == 200, response.text
    entries: list[dict[str, Any]] = response.json()["conversations"]
    return entries


class RecordedSends:
    # Stands in for step one of the agent, records each call, and refuses
    # the message as busy, so that a test can see whether a request reached
    # the agent module.
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def begin_answer(self, conversation_id: str, message_text: str) -> Any:
        self.calls.append((conversation_id, message_text))
        raise ConversationBusyError("Refused by the test.")


class PiecesThenError:
    # Stands in for the Answer of the agent module: gives some pieces, then
    # raises an error of the module, and records whether it was closed.
    def __init__(self, pieces: list[str], error: AgentError) -> None:
        self._pieces = list(pieces)
        self._error = error
        self.closed = False

    def __aiter__(self) -> "PiecesThenError":
        return self

    async def __anext__(self) -> str:
        if self._pieces:
            return self._pieces.pop(0)
        raise self._error

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture
def small_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    # Used with "usefixtures", which pytest sets up before the client, so the
    # application reads these values when it starts.
    monkeypatch.setenv("POC_TITLE_CHARACTERS", str(SMALL_TITLE_CHARACTERS))
    monkeypatch.setenv(
        "POC_LONGEST_MESSAGE_CHARACTERS", str(SMALL_LONGEST_MESSAGE_CHARACTERS)
    )


@pytest.mark.usefixtures("model_key")
def test_the_pieces_arrive_as_separate_messages_in_order(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    # Line breaks and text that is not ASCII must arrive unchanged.
    pieces = ["**Yes**", ", line one\n", "line two — 你好", "\n\n", "Ende."]
    stand_in.answer(*pieces)
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    messages = send(client, token, conversation_id, "Two lines, please.")

    assert messages == [text(piece) for piece in pieces] + [END]


@pytest.mark.usefixtures("model_key")
def test_the_pieces_are_delivered_while_the_answer_is_written(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    held = stand_in.answer_and_hold("one ", "two ", "three", hold_after=2)
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    with client.stream(
        "POST",
        messages_address(conversation_id),
        json={"text": "Count to three."},
        headers=bearer(token),
    ) as response:
        assert response.status_code == 200
        messages = read_messages(response.iter_lines())
        # The stand-in holds the rest, so these two pieces can only have
        # come while the answer is still being written.
        assert [next(messages), next(messages)] == [text("one "), text("two ")]
        assert not held.finished.is_set()
        assert held.pieces_sent == 2
        held.let_go()
        assert list(messages) == [text("three"), END]


@pytest.mark.usefixtures("model_key")
def test_after_a_complete_answer_the_history_holds_the_message_and_the_answer(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    user_text = "  What colour\nis the sky?  "
    stand_in.answer("Blue ", "and white.")
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    send(client, token, conversation_id, user_text)
    response = client.get(messages_address(conversation_id), headers=bearer(token))

    assert response.status_code == 200
    # The text reaches the agent as the user wrote it, not trimmed.
    assert response.json() == {
        "messages": [
            {"role": "user", "text": user_text},
            {"role": "assistant", "text": "Blue and white."},
        ]
    }


def test_a_provider_error_becomes_an_error_message_and_the_stream_closes(
    model_key: str,
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    # 400 comes back at once; the runtime tries 401 and 500 again for
    # seconds. The stand-in repeats the key in its error text.
    stand_in.fail(400, echo_key=True)
    stand_in.answer("Working ", "again.")
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    with client.stream(
        "POST",
        messages_address(conversation_id),
        json={"text": "This one fails."},
        headers=bearer(token),
    ) as response:
        assert response.status_code == 200
        raw_stream = response.read().decode()

    messages = list(read_messages(raw_stream.split("\n")))
    # One error message, the last one, and no end after it.
    assert messages == [FAILED]
    assert "on purpose" not in raw_stream
    error_lines = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.ERROR
    ]
    failed_lines = [line for line in error_lines if conversation_id in line]
    assert len(failed_lines) == 1
    assert "The stand-in answers 400 on purpose" in failed_lines[0]
    assert "ModelProviderError" in failed_lines[0]
    assert "provider status: 400" in failed_lines[0]
    assert all(model_key not in line for line in error_lines)
    # The same conversation takes a new message.
    assert send(client, token, conversation_id, "Try again.") == [
        text("Working "),
        text("again."),
        END,
    ]


def test_an_error_after_some_pieces_ends_the_stream_with_the_error(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    error_text = secrets.token_hex(8)
    answer = PiecesThenError(["Half ", "an "], AgentError(error_text))

    async def begin_answer(conversation_id: str, message_text: str) -> Any:
        return answer

    monkeypatch.setattr(the_agent(), "begin_answer", begin_answer)

    with client.stream(
        "POST",
        messages_address(conversation_id),
        json={"text": "Hello"},
        headers=bearer(token),
    ) as response:
        assert response.status_code == 200
        raw_stream = response.read().decode()

    assert list(read_messages(raw_stream.split("\n"))) == [
        text("Half "),
        text("an "),
        FAILED,
    ]
    assert error_text not in raw_stream
    assert any(
        record.levelno == logging.ERROR and error_text in record.getMessage()
        for record in caplog.records
    )
    assert answer.closed


def test_another_users_conversation_and_unknown_ids_get_the_same_404(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alice_token = sign_in(add_user("alice"))
    bob_token = sign_in(add_user("bob"))
    bobs_id = start_conversation(client, bob_token)["id"]
    recorded = RecordedSends()
    monkeypatch.setattr(the_agent(), "begin_answer", recorded.begin_answer)
    rows_before = conversation_rows(database_file)
    # The answer of the history endpoint for a conversation of another user.
    history_answer = client.get(messages_address(bobs_id), headers=bearer(alice_token))
    expected = (404, history_answer.json())
    assert expected == (404, {"detail": "Conversation not found"})

    answers = []
    for conversation_id in (bobs_id, secrets.token_hex(16), "not-a-conversation-id"):
        response = client.post(
            messages_address(conversation_id),
            json={"text": "Hello"},
            headers=bearer(alice_token),
        )
        answers.append((response.status_code, response.json()))

    assert answers == [expected, expected, expected]
    assert recorded.calls == []
    assert conversation_rows(database_file) == rows_before
    # Shows that the stand-in of step one is called for the owner.
    response = client.post(
        messages_address(bobs_id), json={"text": "Hello"}, headers=bearer(bob_token)
    )
    assert response.status_code == 409
    assert recorded.calls == [(bobs_id, "Hello")]


@pytest.mark.usefixtures("model_key")
def test_the_first_message_sets_the_title_and_a_later_one_keeps_it(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
) -> None:
    stand_in.answer("Sure.")
    stand_in.answer("Fine.")
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    send(client, token, conversation_id, "  Plans\n\nfor   the\tweekend \r\n ")
    send(client, token, conversation_id, "Something else entirely")

    assert conversation_row(database_file, conversation_id)["title"] == (
        "Plans for the weekend"
    )
    assert [entry["title"] for entry in list_entries(client, token)] == [
        "Plans for the weekend"
    ]


@pytest.mark.usefixtures("small_limits", "model_key")
def test_the_title_keeps_as_many_characters_as_the_setting(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    stand_in.answer("Sure.")
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    send(client, token, conversation_id, "A first message\nthat is long")

    # The first 12 characters, with nothing added to mark the cut.
    assert [entry["title"] for entry in list_entries(client, token)] == ["A first mess"]


@pytest.mark.usefixtures("model_key")
def test_a_message_sets_the_time_of_the_last_activity(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
) -> None:
    stand_in.answer("Sure.")
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    before = conversation_row(database_file, conversation_id)

    send(client, token, conversation_id, "Hello")

    after = conversation_row(database_file, conversation_id)
    # The stored form is text that sorts in the order of time.
    assert after["last_active_at"] > before["last_active_at"]
    assert after["created_at"] == before["created_at"]
    assert re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z", after["last_active_at"]
    )


@pytest.mark.usefixtures("model_key")
def test_the_conversation_with_the_latest_message_comes_first(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    stand_in.answer("One.")
    stand_in.answer("Two.")
    token = sign_in(add_user("alice"))
    older = start_conversation(client, token)["id"]
    newer = start_conversation(client, token)["id"]
    assert [entry["id"] for entry in list_entries(client, token)] == [newer, older]

    send(client, token, older, "Back to the older one")
    assert [entry["id"] for entry in list_entries(client, token)] == [older, newer]

    send(client, token, newer, "And the newer one")
    assert [entry["id"] for entry in list_entries(client, token)] == [newer, older]


@pytest.mark.usefixtures("model_key")
def test_a_reader_that_goes_away_stops_the_answer_and_frees_the_conversation(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    held = stand_in.answer_and_hold("one ", "two ", "three", hold_after=1)
    stand_in.answer("A new ", "answer.")
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    with client.stream(
        "POST",
        messages_address(conversation_id),
        json={"text": "Count to three."},
        headers=bearer(token),
    ) as response:
        assert next(read_messages(response.iter_lines())) == text("one ")
    # Leaving the block closes the connection while the stand-in holds.

    # The runtime closes its request to the stand-in: the model is stopped.
    assert held.connection_closed_early.wait(STAND_IN_WAIT_SECONDS)
    assert held.pieces_sent == 1
    portal_of(client).call(wait_until_free, the_agent(), conversation_id)
    # The same conversation takes a new message, with no 409.
    assert send(client, token, conversation_id, "Something else.") == [
        text("A new "),
        text("answer."),
        END,
    ]


@pytest.mark.usefixtures("model_key")
def test_a_message_to_a_conversation_that_is_answering_gets_409(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    held = stand_in.answer_and_hold("First ", "answer.", hold_after=1)
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    with client.stream(
        "POST",
        messages_address(conversation_id),
        json={"text": "First message"},
        headers=bearer(token),
    ) as response:
        messages = read_messages(response.iter_lines())
        assert next(messages) == text("First ")

        second = client.post(
            messages_address(conversation_id),
            json={"text": "Second message"},
            headers=bearer(token),
        )

        held.let_go()
        assert list(messages) == [text("answer."), END]

    assert second.status_code == 409
    assert second.json() == {"detail": BUSY_TEXT}
    requests = stand_in.message_requests()
    assert len(requests) == 1
    assert "Second message" not in requests[0].all_text()


@pytest.mark.usefixtures("stand_in_address")
def test_with_no_model_key_a_message_gets_503_and_changes_nothing(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    rows_before = conversation_rows(database_file)

    response = client.post(
        messages_address(conversation_id),
        json={"text": "Hello"},
        headers=bearer(token),
    )

    assert response.status_code == 503
    # The text of its own, and not the general text of a failure.
    assert response.json() == {"detail": NO_MODEL_KEY_TEXT}
    assert NO_MODEL_KEY_TEXT != FAILED_TEXT
    assert conversation_rows(database_file) == rows_before
    assert any(
        record.levelno == logging.ERROR and "NoModelKeyError" in record.getMessage()
        for record in caplog.records
    )
    assert stand_in.message_requests() == []


@pytest.mark.usefixtures("small_limits")
@pytest.mark.parametrize(
    "body",
    [
        {"text": ""},
        {"text": " \n\t  "},
        {"text": "x" * (SMALL_LONGEST_MESSAGE_CHARACTERS + 1)},
        {},
        {"text": 12345},
    ],
    ids=["empty", "white space", "too long", "no text", "not a string"],
)
def test_a_body_that_is_not_valid_gets_422_and_reaches_nothing(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    body: dict[str, Any],
) -> None:
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    recorded = RecordedSends()
    monkeypatch.setattr(the_agent(), "begin_answer", recorded.begin_answer)
    rows_before = conversation_rows(database_file)

    response = client.post(
        messages_address(conversation_id), json=body, headers=bearer(token)
    )

    assert response.status_code == 422
    # The shape that FastAPI gives a body that fails validation.
    answer = response.json()
    assert set(answer) == {"detail"}
    assert isinstance(answer["detail"], list)
    assert len(answer["detail"]) >= 1
    for entry in answer["detail"]:
        assert {"loc", "msg", "type"} <= set(entry)
        assert entry["loc"][0] == "body"
    assert recorded.calls == []
    assert conversation_rows(database_file) == rows_before


@pytest.mark.usefixtures("small_limits")
def test_a_message_that_is_too_long_is_not_repeated_and_the_limit_is_named(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    # 40 characters made at run time, so the test can look for them.
    long_text = secrets.token_hex(20)

    response = client.post(
        messages_address(conversation_id),
        json={"text": long_text},
        headers=bearer(token),
    )

    assert response.status_code == 422
    assert long_text not in response.text
    [entry] = response.json()["detail"]
    assert entry["loc"] == ["body", "text"]
    assert str(SMALL_LONGEST_MESSAGE_CHARACTERS) in entry["msg"]
    # The limit as a number, for a frontend that does not read the sentence.
    assert entry["ctx"] == {"max_length": SMALL_LONGEST_MESSAGE_CHARACTERS}


@pytest.mark.usefixtures("small_limits", "model_key")
def test_the_limit_counts_characters_not_bytes(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    # Each of these characters takes three bytes in UTF-8.
    stand_in.answer("Fine.")
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]

    too_long = client.post(
        messages_address(conversation_id),
        json={"text": "你" * (SMALL_LONGEST_MESSAGE_CHARACTERS + 1)},
        headers=bearer(token),
    )
    assert too_long.status_code == 422

    messages = send(
        client, token, conversation_id, "你" * SMALL_LONGEST_MESSAGE_CHARACTERS
    )
    assert messages == [text("Fine."), END]


@pytest.mark.usefixtures("small_limits")
@pytest.mark.parametrize(
    "bad_text",
    ["   ", "x" * (SMALL_LONGEST_MESSAGE_CHARACTERS + 1)],
    ids=["white space", "too long"],
)
def test_a_body_that_is_not_valid_gets_422_whatever_the_conversation(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    bad_text: str,
) -> None:
    alice_token = sign_in(add_user("alice"))
    bob_token = sign_in(add_user("bob"))
    bobs_id = start_conversation(client, bob_token)["id"]
    alices_id = start_conversation(client, alice_token)["id"]

    answers = []
    for conversation_id in (
        alices_id,
        bobs_id,
        secrets.token_hex(16),
        "not-a-conversation-id",
    ):
        response = client.post(
            messages_address(conversation_id),
            json={"text": bad_text},
            headers=bearer(alice_token),
        )
        answers.append((response.status_code, response.json()))

    assert answers[0][0] == 422
    assert all(answer == answers[0] for answer in answers)


def test_another_error_of_step_one_gets_500_and_goes_to_the_log(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    error_text = secrets.token_hex(8)

    async def begin_answer(conversation_id: str, message_text: str) -> Any:
        raise AgentError(error_text)

    monkeypatch.setattr(the_agent(), "begin_answer", begin_answer)
    rows_before = conversation_rows(database_file)

    response = client.post(
        messages_address(conversation_id),
        json={"text": "Hello"},
        headers=bearer(token),
    )

    assert response.status_code == 500
    assert response.json() == {"detail": FAILED_TEXT}
    assert error_text not in response.text
    assert any(
        record.levelno == logging.ERROR and error_text in record.getMessage()
        for record in caplog.records
    )
    assert conversation_rows(database_file) == rows_before


@pytest.mark.usefixtures("model_key")
def test_a_failed_database_write_after_step_one_leaves_the_conversation_free(
    stand_in: ModelStandIn,
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
    database_file: Path,
) -> None:
    stand_in.answer("Fine.")
    token = sign_in(add_user("alice"))
    conversation_id = start_conversation(client, token)["id"]
    # A trigger makes SQLite refuse every change to a row of conversations,
    # so the write after step one fails.
    run_sql(
        database_file,
        "CREATE TRIGGER refuse_updates BEFORE UPDATE ON conversations "
        "BEGIN SELECT RAISE(ABORT, 'refused by the test'); END",
    )

    # The test client raises the error of the application, which is the
    # plain 500 of the framework for a browser.
    with pytest.raises(sqlite3.Error, match="refused by the test"):
        client.post(
            messages_address(conversation_id),
            json={"text": "Hello"},
            headers=bearer(token),
        )

    run_sql(database_file, "DROP TRIGGER refuse_updates")
    # Not refused with 409: the answer of step one was closed.
    assert send(client, token, conversation_id, "Hello again") == [
        text("Fine."),
        END,
    ]
    # The failed message never reached the model.
    requests = stand_in.message_requests()
    assert len(requests) == 1
    assert "Hello again" in requests[0].all_text()


def test_the_api_documentation_describes_the_endpoint_and_the_format(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/conversations/{conversation_id}/messages"]["post"]
    components = schema["components"]["schemas"]

    assert operation["summary"]
    description = operation["description"]
    assert "exactly one" in description
    assert "colon" in description
    assert "skips" in description

    body_schema = operation["requestBody"]["content"]["application/json"]["schema"]
    body_model = components[body_schema["$ref"].rsplit("/", 1)[-1]]
    assert body_model["required"] == ["text"]
    assert body_model["properties"]["text"]["description"]

    stream = operation["responses"]["200"]["content"]["text/event-stream"]
    content_schema = stream["itemSchema"]["properties"]["data"]["contentSchema"]
    mapping = content_schema["discriminator"]["mapping"]
    assert content_schema["discriminator"]["propertyName"] == "type"
    assert set(mapping) == {"text", "end", "error"}
    for kind, reference in mapping.items():
        model = components[reference.rsplit("/", 1)[-1]]
        assert model["description"], kind
        assert model["properties"]["type"]["const"] == kind
        assert "type" in model["required"]
        for name, field in model["properties"].items():
            assert field["description"], f"{kind}.{name}"

    for status_code in ("404", "409", "422", "500", "503"):
        answer = operation["responses"][status_code]
        assert answer["description"], status_code
        # The error answers are JSON, not a stream.
        assert set(answer["content"]) == {"application/json"}, status_code

    assert client.get("/docs").status_code == 200
