# Tests of backend/app/agent.py, the one module that touches the SDK. They run
# the real SDK and its runtime against the local stand-in for the model
# provider in backend/tests/model_stand_in.py, so they need no model key.
#
# pytest has no built-in support for "async def" tests, so each test is a
# plain function that runs its steps with asyncio.run().
import asyncio
import contextlib
import secrets
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import pytest
from conftest import STAND_IN_WAIT_SECONDS, portal_of, wait_until_free
from fastapi.testclient import TestClient
from model_stand_in import ModelStandIn

from app import agent as agent_module
from app.agent import (
    Agent,
    AgentError,
    Answer,
    AnswerTimedOutError,
    ConversationBusyError,
    HistoryMessage,
    InvalidConversationIdError,
    ModelProviderError,
    NoModelKeyError,
    UnknownConversationError,
)
from app.config import Settings
from app.main import app


@asynccontextmanager
async def started_agent() -> AsyncIterator[Agent]:
    # One agent stands for one run of the backend. Stopping it and making a
    # new one over the same session folder stands for a restart.
    agent = Agent(Settings())
    await agent.start()
    try:
        yield agent
    finally:
        await agent.stop()


class MovedClock:
    # Stands in for the module "time" inside backend/app/agent.py. Only the
    # agent module sees it; the event loop keeps the real clock.
    def __init__(self) -> None:
        self._moved_by = 0.0

    def monotonic(self) -> float:
        return time.monotonic() + self._moved_by

    def move_on(self, seconds: float) -> None:
        self._moved_by += seconds


async def read_all(answer: Answer) -> list[str]:
    return [piece async for piece in answer]


async def send(agent: Agent, conversation_id: str, text: str) -> list[str]:
    return await read_all(await agent.begin_answer(conversation_id, text))


async def wait_for(event: threading.Event) -> None:
    # The stand-in runs in its own thread and signals with threading.Event.
    seen = await asyncio.to_thread(event.wait, STAND_IN_WAIT_SECONDS)
    assert seen, "the stand-in did not see what the test waited for"


@pytest.mark.usefixtures("model_key")
def test_the_pieces_arrive_in_order(stand_in: ModelStandIn) -> None:
    pieces = ["The ", "sky ", "is ", "blue", "."]
    stand_in.answer(*pieces)

    async def steps() -> list[str]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            return await send(agent, conversation_id, "What colour is the sky?")

    assert asyncio.run(steps()) == pieces


@pytest.mark.usefixtures("model_key")
def test_a_conversation_continues_after_a_restart(stand_in: ModelStandIn) -> None:
    stand_in.answer("Maple ", "is noted.")
    stand_in.answer("You asked about maple.")

    async def first_run() -> str:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            await send(agent, conversation_id, "Remember the word maple.")
            return conversation_id

    async def second_run(conversation_id: str) -> list[HistoryMessage]:
        async with started_agent() as agent:
            history = await agent.read_history(conversation_id)
            await send(agent, conversation_id, "Which word did I give you?")
            return history

    conversation_id = asyncio.run(first_run())
    history = asyncio.run(second_run(conversation_id))

    assert history == [
        HistoryMessage(role="user", text="Remember the word maple."),
        HistoryMessage(role="assistant", text="Maple is noted."),
    ]
    second_request = stand_in.message_requests()[-1].message_texts()
    assert [role for role, _ in second_request] == ["user", "assistant", "user"]
    assert second_request[0][1].endswith("Remember the word maple.")
    assert second_request[1][1] == "Maple is noted."
    assert second_request[2][1].endswith("Which word did I give you?")


@pytest.mark.usefixtures("model_key")
def test_a_second_message_while_answering_is_refused(stand_in: ModelStandIn) -> None:
    held = stand_in.answer_and_hold("First ", "answer.", hold_after=1)

    async def steps() -> None:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            answer = await agent.begin_answer(conversation_id, "First message")
            assert await anext(answer) == "First "

            with pytest.raises(ConversationBusyError):
                await agent.begin_answer(conversation_id, "Second message")

            held.let_go()
            assert await read_all(answer) == ["answer."]

    asyncio.run(steps())

    requests = stand_in.message_requests()
    assert len(requests) == 1
    assert "Second message" not in requests[0].all_text()


@pytest.mark.usefixtures("model_key")
def test_a_new_conversation_has_an_empty_history() -> None:
    async def steps() -> list[HistoryMessage]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            return await agent.read_history(conversation_id)

    assert asyncio.run(steps()) == []


@pytest.mark.usefixtures("model_key")
def test_the_history_gives_the_texts_as_sent(stand_in: ModelStandIn) -> None:
    # Line breaks, Markdown and other scripts must come back unchanged.
    user_text = "Two lines:\n  *one* and `two` — 你好"
    stand_in.answer("**Yes**", ", line one\n", "line two.")

    async def steps() -> list[HistoryMessage]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            await send(agent, conversation_id, user_text)
            return await agent.read_history(conversation_id)

    assert asyncio.run(steps()) == [
        HistoryMessage(role="user", text=user_text),
        HistoryMessage(role="assistant", text="**Yes**, line one\nline two."),
    ]


@pytest.mark.usefixtures("model_key")
def test_a_conversation_with_no_message_takes_its_first_message_after_a_restart(
    stand_in: ModelStandIn,
) -> None:
    stand_in.answer("Hello ", "after the restart.")

    async def first_run() -> str:
        async with started_agent() as agent:
            return await agent.start_conversation()

    async def second_run(conversation_id: str) -> list[str]:
        async with started_agent() as agent:
            assert await agent.read_history(conversation_id) == []
            return await send(agent, conversation_id, "Hello")

    conversation_id = asyncio.run(first_run())

    assert asyncio.run(second_run(conversation_id)) == ["Hello ", "after the restart."]


@pytest.mark.usefixtures("model_key")
def test_closing_the_answer_early_stops_the_model(stand_in: ModelStandIn) -> None:
    held = stand_in.answer_and_hold("one ", "two ", "three ", "four", hold_after=2)
    stand_in.answer("A new ", "answer.")

    async def steps() -> tuple[list[str], list[str], list[HistoryMessage]]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            answer = await agent.begin_answer(conversation_id, "Count to four.")
            read = [await anext(answer), await anext(answer)]
            await answer.aclose()
            # The runtime closes its request to the stand-in.
            await wait_for(held.connection_closed_early)
            # No more pieces come from a closed answer.
            with pytest.raises(StopAsyncIteration):
                await anext(answer)
            next_answer = await send(agent, conversation_id, "Something else.")
            return read, next_answer, await agent.read_history(conversation_id)

    read, next_answer, history = asyncio.run(steps())

    assert read == ["one ", "two "]
    assert held.pieces_sent == 2
    assert next_answer == ["A new ", "answer."]
    # What the history holds after a stop: the user's message, and no part
    # of the stopped answer.
    assert history == [
        HistoryMessage(role="user", text="Count to four."),
        HistoryMessage(role="user", text="Something else."),
        HistoryMessage(role="assistant", text="A new answer."),
    ]


@pytest.mark.usefixtures("model_key")
def test_cancelling_the_reading_task_stops_the_model(stand_in: ModelStandIn) -> None:
    # This is what happens when a browser leaves a streaming response.
    held = stand_in.answer_and_hold("one ", "two ", "three ", "four", hold_after=2)
    stand_in.answer("A new ", "answer.")

    async def steps() -> tuple[list[str], list[str]]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            answer = await agent.begin_answer(conversation_id, "Count to four.")
            read: list[str] = []
            two_read = asyncio.Event()

            async def reader() -> None:
                async for piece in answer:
                    read.append(piece)
                    if len(read) == 2:
                        two_read.set()

            reading = asyncio.create_task(reader())
            await two_read.wait()
            reading.cancel()
            with pytest.raises(asyncio.CancelledError):
                await reading
            await wait_for(held.connection_closed_early)
            next_answer = await send(agent, conversation_id, "Something else.")
            return read, next_answer

    read, next_answer = asyncio.run(steps())

    assert read == ["one ", "two "]
    assert held.pieces_sent == 2
    assert next_answer == ["A new ", "answer."]


@pytest.mark.usefixtures("model_key")
def test_a_cancel_scope_like_starlettes_stops_the_model(stand_in: ModelStandIn) -> None:
    # Starlette reads a streaming response in an anyio task group, and
    # cancels the group's scope when the browser leaves. A cancelled scope
    # raises the cancellation again at every wait inside it, not only once.
    held = stand_in.answer_and_hold("one ", "two ", "three ", "four", hold_after=2)
    stand_in.answer("A new ", "answer.")

    async def steps() -> tuple[list[str], list[HistoryMessage], list[str]]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            answer = await agent.begin_answer(conversation_id, "Count to four.")
            read: list[str] = []
            two_read = anyio.Event()

            async def reader() -> None:
                async for piece in answer:
                    read.append(piece)
                    if len(read) == 2:
                        two_read.set()

            async with anyio.create_task_group() as group:
                group.start_soon(reader)
                await two_read.wait()
                group.cancel_scope.cancel()

            await wait_for(held.connection_closed_early)
            await wait_until_free(agent, conversation_id)
            # The clean-up must have disconnected the session. Nothing public
            # shows an open session, so the test reads private state of the
            # agent and of the SDK's client. It does not import the SDK.
            assert agent._client is not None
            assert len(agent._client._sessions) == 0
            history = await agent.read_history(conversation_id)
            next_answer = await send(agent, conversation_id, "Something else.")
            return read, history, next_answer

    read, history, next_answer = asyncio.run(steps())

    assert read == ["one ", "two "]
    assert held.pieces_sent == 2
    assert history == [HistoryMessage(role="user", text="Count to four.")]
    assert next_answer == ["A new ", "answer."]


@pytest.mark.usefixtures("model_key")
def test_stopping_the_agent_while_an_answer_is_open_gives_no_sdk_error(
    stand_in: ModelStandIn,
) -> None:
    stand_in.answer_and_hold("one ", "two ", hold_after=1)
    stand_in.answer_and_hold("three ", "four ", hold_after=1)

    async def steps() -> None:
        agent = Agent(Settings())
        await agent.start()
        first_id = await agent.start_conversation()
        second_id = await agent.start_conversation()
        # One answer is read and closed after the stop, the other is read on.
        to_close = await agent.begin_answer(first_id, "First")
        assert await anext(to_close) == "one "
        to_read = await agent.begin_answer(second_id, "Second")
        assert await anext(to_read) == "three "

        await agent.stop()

        # Each may end cleanly or with an error of this module. An error of
        # the SDK would fail the test.
        with contextlib.suppress(AgentError):
            await to_close.aclose()
        rest: list[str] = []
        with contextlib.suppress(AgentError):
            rest = await read_all(to_read)
        # The end comes at once, with no piece the model sent after the stop.
        assert rest == []

    asyncio.run(steps())


@pytest.mark.usefixtures("model_key")
def test_a_history_read_that_waits_while_the_agent_stops_ends_with_an_agent_error(
    stand_in: ModelStandIn,
) -> None:
    # The answer is read on while the agent stops. Its clean-up frees the
    # conversation during the stop, and the waiting read wakes then. The read
    # ends at the module's own "not started" check, before it reaches the
    # SDK. So this test does not show that a plain RuntimeError of the SDK is
    # turned into an error of the module: no test shows that on its own.
    stand_in.answer_and_hold("one ", "two ", hold_after=1)

    async def steps() -> None:
        agent = Agent(Settings())
        await agent.start()
        conversation_id = await agent.start_conversation()
        answer = await agent.begin_answer(conversation_id, "Question")
        assert await anext(answer) == "one "
        reading_answer = asyncio.create_task(read_all(answer))
        reading_history = asyncio.create_task(agent.read_history(conversation_id))
        for _ in range(10):
            await asyncio.sleep(0)
        assert not reading_history.done()

        await agent.stop()

        with contextlib.suppress(AgentError):
            await reading_answer
        # The read ends with an error of this module.
        with pytest.raises(AgentError):
            await reading_history

    asyncio.run(steps())


@pytest.mark.usefixtures("model_key")
def test_a_history_read_that_wakes_after_the_stop_starts_no_runtime(
    stand_in: ModelStandIn,
) -> None:
    # The answer stays unread through the stop, and is closed afterwards.
    # That frees the conversation, and the waiting read wakes after the stop.
    stand_in.answer_and_hold("one ", "two ", hold_after=1)

    async def steps() -> None:
        agent = Agent(Settings())
        await agent.start()
        # A stopped SDK client starts a new runtime by itself when it is
        # called. Only private state of the SDK's client shows whether a
        # runtime runs, so the test keeps a reference to that client.
        sdk_client = agent._client
        assert sdk_client is not None
        conversation_id = await agent.start_conversation()
        answer = await agent.begin_answer(conversation_id, "Question")
        assert await anext(answer) == "one "
        reading_history = asyncio.create_task(agent.read_history(conversation_id))
        for _ in range(10):
            await asyncio.sleep(0)
        assert not reading_history.done()

        await agent.stop()
        with contextlib.suppress(AgentError):
            await answer.aclose()

        with pytest.raises(AgentError, match="not started"):
            await reading_history
        assert sdk_client._state == "disconnected"
        assert sdk_client._ffi_host is None

    asyncio.run(steps())


@pytest.mark.usefixtures("model_key")
def test_closing_an_answer_before_reading_it_frees_the_conversation(
    stand_in: ModelStandIn,
) -> None:
    stand_in.answer("Answered.")

    async def steps() -> list[str]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            unread = await agent.begin_answer(conversation_id, "Never sent.")
            await unread.aclose()
            return await send(agent, conversation_id, "Sent.")

    assert asyncio.run(steps()) == ["Answered."]
    requests = stand_in.message_requests()
    assert len(requests) == 1
    assert "Never sent." not in requests[0].all_text()


def test_an_answer_that_is_never_read_frees_the_conversation_after_the_wait(
    monkeypatch: pytest.MonkeyPatch, model_key: str, stand_in: ModelStandIn
) -> None:
    # A caller that fails between the two steps must not block the
    # conversation for ever. The clock of the module is moved past the wait
    # setting instead of waiting, so the real message keeps the usual wait
    # and a slow machine cannot fail the test.
    clock = MovedClock()
    monkeypatch.setattr(agent_module, "time", clock)
    stand_in.answer("Answered.")

    async def steps() -> list[str]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            await agent.begin_answer(conversation_id, "Never read.")
            with pytest.raises(ConversationBusyError):
                await agent.begin_answer(conversation_id, "Too early.")
            clock.move_on(Settings().answer_wait_seconds + 1)
            return await send(agent, conversation_id, "After the wait.")

    assert asyncio.run(steps()) == ["Answered."]
    assert len(stand_in.message_requests()) == 1


@pytest.mark.parametrize("message_before", [False, True])
def test_a_provider_error_reaches_the_reader_without_the_key(
    model_key: str, stand_in: ModelStandIn, message_before: bool
) -> None:
    # The stand-in repeats the key in its error, as a careless provider
    # might. With message_before False, the very first message fails.
    if message_before:
        stand_in.answer("Fine.")
    stand_in.fail(400, echo_key=True)
    stand_in.answer("Working ", "again.")

    async def steps() -> tuple[ModelProviderError, list[str]]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            if message_before:
                await send(agent, conversation_id, "Before")
            with pytest.raises(ModelProviderError) as error:
                await send(agent, conversation_id, "This one fails.")
            return error.value, await send(agent, conversation_id, "Try again.")

    error, next_answer = asyncio.run(steps())

    assert error.status_code == 400
    assert "400" in str(error)
    assert model_key not in str(error)
    assert model_key not in repr(error)
    assert next_answer == ["Working ", "again."]


def test_a_silent_provider_ends_the_answer_with_a_time_out(
    monkeypatch: pytest.MonkeyPatch, model_key: str, stand_in: ModelStandIn
) -> None:
    # One second leaves room for a slow machine in the message that follows,
    # which runs under the same setting.
    monkeypatch.setenv("POC_ANSWER_WAIT_SECONDS", "1")
    silent = stand_in.stay_silent()
    stand_in.answer("Back ", "again.")

    async def steps() -> list[str]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            with pytest.raises(AnswerTimedOutError):
                await send(agent, conversation_id, "Hello?")
            await wait_for(silent.connection_closed_early)
            return await send(agent, conversation_id, "Hello again.")

    assert asyncio.run(steps()) == ["Back ", "again."]


@pytest.mark.usefixtures("model_key")
def test_two_conversations_answer_at_the_same_time(stand_in: ModelStandIn) -> None:
    held = stand_in.answer_and_hold("Slow ", "answer.", hold_after=1)

    async def steps() -> tuple[list[str], list[str]]:
        async with started_agent() as agent:
            slow_id = await agent.start_conversation()
            quick_id = await agent.start_conversation()
            slow = await agent.begin_answer(slow_id, "Slow question")
            assert await anext(slow) == "Slow "
            # The slow answer is held open while the quick one is answered.
            stand_in.answer("Quick ", "answer.")
            quick_pieces = await send(agent, quick_id, "Quick question")
            assert not held.finished.is_set()
            held.let_go()
            return quick_pieces, ["Slow ", *await read_all(slow)]

    quick_pieces, slow_pieces = asyncio.run(steps())

    assert quick_pieces == ["Quick ", "answer."]
    assert slow_pieces == ["Slow ", "answer."]


def test_a_request_holds_only_its_own_conversation_and_the_settings(
    monkeypatch: pytest.MonkeyPatch, model_key: str, stand_in: ModelStandIn
) -> None:
    system_prompt = f"Test prompt {secrets.token_hex(4)}"
    model_name = f"test-model-{secrets.token_hex(4)}"
    monkeypatch.setenv("POC_SYSTEM_PROMPT", system_prompt)
    monkeypatch.setenv("POC_MODEL_NAME", model_name)
    first_word = f"first{secrets.token_hex(4)}"
    first_answer = f"answer{secrets.token_hex(4)}"
    stand_in.answer(first_answer)
    stand_in.answer("Other answer.")

    async def steps() -> None:
        async with started_agent() as agent:
            first_id = await agent.start_conversation()
            other_id = await agent.start_conversation()
            await send(agent, first_id, f"My word is {first_word}.")
            await send(agent, other_id, "What is my word?")

    asyncio.run(steps())

    other_request = stand_in.message_requests()[-1]
    assert first_word not in other_request.all_text()
    assert first_answer not in other_request.all_text()
    assert other_request.system_prompt() == system_prompt
    assert other_request.body["model"] == model_name
    # The key reaches the provider in the request header, and only there.
    assert other_request.headers["x-api-key"] == model_key


@pytest.mark.usefixtures("stand_in_address")
def test_with_no_model_key_the_application_starts_and_sending_is_refused(
    stand_in: ModelStandIn,
) -> None:
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        agent: Agent = app.state.agent
        conversation_id = portal_of(client).call(agent.start_conversation)

        with pytest.raises(NoModelKeyError):
            portal_of(client).call(agent.begin_answer, conversation_id, "Hello")

    assert stand_in.requests == []


@pytest.mark.parametrize(
    "conversation_id",
    [
        "../../etc",
        "a/b",
        "..",
        "",
        "0123456789abcdef0123456789abcde/",
        "0123456789ABCDEF0123456789ABCDEF",
        "0123456789abcdef0123456789abcdef\n",
        "session-state",
    ],
)
def test_an_id_the_module_did_not_make_is_refused_before_the_sdk(
    conversation_id: str,
) -> None:
    # The agent is not started. An action that reached the SDK would fail
    # with "not started"; refusing the id comes first.
    agent = Agent(Settings())

    async def steps() -> None:
        with pytest.raises(InvalidConversationIdError):
            await agent.begin_answer(conversation_id, "Hello")
        with pytest.raises(InvalidConversationIdError):
            await agent.read_history(conversation_id)

    asyncio.run(steps())


@pytest.mark.usefixtures("model_key")
def test_an_id_with_a_path_in_it_does_not_reach_the_session_folder(
    session_directory: Path, stand_in: ModelStandIn
) -> None:
    async def steps() -> None:
        async with started_agent() as agent:
            for conversation_id in ("../outside", "inside/../../outside"):
                with pytest.raises(InvalidConversationIdError):
                    await agent.begin_answer(conversation_id, "Hello")
                with pytest.raises(InvalidConversationIdError):
                    await agent.read_history(conversation_id)

    asyncio.run(steps())

    assert not (session_directory.parent / "outside").exists()
    assert stand_in.requests == []


@pytest.mark.usefixtures("model_key")
def test_an_unknown_conversation_is_refused(stand_in: ModelStandIn) -> None:
    unknown_id = secrets.token_hex(16)

    async def steps() -> None:
        async with started_agent() as agent:
            with pytest.raises(UnknownConversationError):
                await agent.begin_answer(unknown_id, "Hello")
            with pytest.raises(UnknownConversationError):
                await agent.read_history(unknown_id)

    asyncio.run(steps())

    assert stand_in.requests == []


@pytest.mark.usefixtures("model_key")
def test_reading_the_history_while_answering_waits_for_the_answer(
    stand_in: ModelStandIn,
) -> None:
    held = stand_in.answer_and_hold("Finished ", "answer.", hold_after=1)

    async def steps() -> list[HistoryMessage]:
        async with started_agent() as agent:
            conversation_id = await agent.start_conversation()
            answer = await agent.begin_answer(conversation_id, "Question")
            assert await anext(answer) == "Finished "
            reading = asyncio.create_task(agent.read_history(conversation_id))
            # Let the read start. It must wait, because the answer is open.
            for _ in range(10):
                await asyncio.sleep(0)
            assert not reading.done()
            held.let_go()
            assert await read_all(answer) == ["answer."]
            return await reading

    assert asyncio.run(steps()) == [
        HistoryMessage(role="user", text="Question"),
        HistoryMessage(role="assistant", text="Finished answer."),
    ]


def test_the_application_starts_the_runtime_and_stops_it(
    session_directory: Path,
) -> None:
    with TestClient(app) as client:
        agent: Agent = app.state.agent
        conversation_id = portal_of(client).call(agent.start_conversation)
        assert portal_of(client).call(agent.read_history, conversation_id) == []

    # The runtime keeps its files in the session folder of the settings.
    assert (session_directory / "session-state" / conversation_id).is_dir()
    with pytest.raises(AgentError, match="not started"):
        asyncio.run(agent.start_conversation())
