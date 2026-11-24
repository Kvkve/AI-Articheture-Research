# The one module that touches the Copilot SDK (the Python package "copilot").
# No other Python file may import the SDK; a ruff rule in
# backend/pyproject.toml enforces this. So the SDK can be replaced by
# changing this one file. No type of the SDK leaves this module: what it gives
# out and what it raises are the small types defined here.
#
# The conversation history lives only in the SDK's session files, one folder
# per conversation. Every action resumes the session from disk, does its work
# and disconnects, so no session stays open in memory between messages.
import asyncio
import contextlib
import logging
import re
import secrets
import time
from collections.abc import AsyncGenerator, Iterator
from dataclasses import dataclass, field
from typing import Literal, cast, get_args

from copilot import (
    CopilotClient,
    CopilotSession,
    JsonRpcError,
    PermissionRequest,
    PermissionRequestResult,
    RuntimeConnection,
)

# ProcessExitedError is what a request raises when the runtime has stopped.
# The SDK does not export it, so it comes from the SDK's internal module. The
# SDK is pinned at one version, so the name cannot move under this code.
from copilot._jsonrpc import ProcessExitedError
from copilot.client import (
    SessionEventOptions,
    SessionGitHubOptions,
    SessionInferenceOptions,
    SessionPermissionOptions,
    SessionToolOptions,
)
from copilot.rpc import PermissionDecisionReject
from copilot.session import (
    NamedProviderConfig,
    PermissionInvocation,
    SystemMessageReplaceConfig,
)
from copilot.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    SessionErrorData,
    SessionEvent,
    SessionEventType,
    UserMessageData,
)

from app.config import Settings

# The provider types that SDK version 2.0.1 accepts. The setting is checked
# against this list when the runtime starts, so a wrong value stops the
# backend with a clear message instead of failing at the first message.
ProviderType = Literal["openai", "azure", "anthropic", "google", "winml"]

# The label of the one provider connection in each session. The runtime uses
# it only to tie the model to the connection.
PROVIDER_LABEL = "provider"

# The error types that a request of SDK 2.0.1 can raise. They are turned
# into errors of this module, so that no type of the SDK leaves it. The SDK
# also raises a plain RuntimeError, for example "Client disconnected during
# session initialization" while its client stops. The conversion is used
# around calls on the SDK only, so it cannot hide a fault of this module.
SDK_ERRORS = (JsonRpcError, ProcessExitedError, RuntimeError)

logger = logging.getLogger(__name__)

# The form of the ids this module makes: 32 small hexadecimal characters.
# The id becomes the name of a folder on disk, so an id of any other form is
# refused before it reaches the SDK.
CONVERSATION_ID_FORM = re.compile(r"[0-9a-f]{32}")


class AgentError(Exception):
    """The base of every error this module raises."""


class InvalidConversationIdError(AgentError):
    """The id does not have the form of the ids this module makes."""


class UnknownConversationError(AgentError):
    """No conversation with this id is stored."""


class ConversationBusyError(AgentError):
    """The conversation is still answering a message."""


class NoModelKeyError(AgentError):
    """No model key is set, so no message can be sent."""


class ModelProviderError(AgentError):
    """The model provider answered with an error."""

    def __init__(self, message: str, status_code: int | None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AnswerTimedOutError(AgentError):
    """No event of the answer arrived within the wait setting."""


@dataclass(frozen=True)
class HistoryMessage:
    role: Literal["user", "assistant"]
    text: str


@dataclass
class _ConversationInUse:
    # Marks a conversation that is answering or whose history is being read.
    # The SDK has no lock, so this module lets one action at a time into a
    # conversation.
    taken_at: float
    # False only between step one of an answer and the first read of it.
    started: bool
    freed: asyncio.Event = field(default_factory=asyncio.Event)


def check_conversation_id(conversation_id: str) -> None:
    if CONVERSATION_ID_FORM.fullmatch(conversation_id) is None:
        raise InvalidConversationIdError("This is not a valid conversation id.")


def _refuse_every_permission(
    request: PermissionRequest, invocation: PermissionInvocation
) -> PermissionRequestResult:
    # The sessions have no tools, so nothing should ask. If the runtime asks
    # anyway, the answer is no.
    return PermissionDecisionReject(feedback="This application allows no tools.")


class Agent:
    """The link to the SDK. One object serves one backend process."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: CopilotClient | None = None
        # Which conversations are answering or being read. A dict in memory
        # fits one backend process only.
        self._in_use: dict[str, _ConversationInUse] = {}
        # The event queues of the answers that are open, so that stopping the
        # agent can end them.
        self._open_answers: set[asyncio.Queue[SessionEvent | None]] = set()
        # The clean-ups that are running. The event loop keeps only a weak
        # reference to a task, so without this set a clean-up whose reader
        # was cancelled could be collected before it ends.
        self._clean_ups: set[asyncio.Task[None]] = set()

    async def start(self) -> None:
        if self._settings.model_provider_type not in get_args(ProviderType):
            raise AgentError(
                "POC_MODEL_PROVIDER_TYPE must be one of: "
                + ", ".join(get_args(ProviderType))
            )
        directory = self._settings.session_directory
        directory.mkdir(parents=True, exist_ok=True)
        client = CopilotClient(
            # "empty" switches off the runtime's features for a coding agent
            # on the host machine, such as file tools and a shared memory.
            mode="empty",
            # The runtime runs inside the backend's own process. This is said
            # here, and not left to an environment variable.
            runtime=RuntimeConnection.for_inprocess(base_directory=str(directory)),
            # The machine may hold a GitHub token in its environment. The
            # runtime must not sign in to GitHub with it.
            github={"use_logged_in_user": False},
        )
        await client.start()
        self._client = client

    async def stop(self) -> None:
        client, self._client = self._client, None
        if client is None:
            return
        # An answer that is being read ends with an error of this module
        # instead of waiting for events that will never come. None in an
        # event queue means "the agent has stopped".
        for events in self._open_answers:
            events.put_nowait(None)
        # Clean-ups that are running get the chance to stop the model and
        # disconnect before the runtime goes away.
        if self._clean_ups:
            await asyncio.wait(
                set(self._clean_ups), timeout=self._settings.answer_wait_seconds
            )
        try:
            await client.stop()
        except ExceptionGroup as errors:
            # The SDK reports each failed step of its stop in a group of its
            # own error type.
            raise AgentError(
                self._without_key(f"The agent runtime did not stop cleanly: {errors}")
            ) from None

    async def start_conversation(self) -> str:
        """Makes a new conversation and returns its id."""
        conversation_id = secrets.token_hex(16)
        client = self._started_client()
        with self._sdk_errors():
            # A name makes the session persist from the start. Without one,
            # the runtime can resume a session only after its first message,
            # and a conversation with no message would not survive a restart.
            session = await client.create_session(
                session_id=conversation_id,
                name=conversation_id,
                model=self._settings.model_name,
                system_message=self._system_message(),
                permissions=self._permissions(),
                inference=self._inference(),
                tools=self._tools(),
                github=self._github(),
                events=self._events(),
            )
        await self._disconnect(session)
        return conversation_id

    async def begin_answer(self, conversation_id: str, text: str) -> "Answer":
        """Step one of sending a message.

        Refuses the message when the conversation is still answering or when
        no model key is set. Nothing reaches the model before step two, which
        is reading the returned Answer with "async for". The caller must read
        the Answer to its end or close it with aclose().
        """
        check_conversation_id(conversation_id)
        self._started_client()
        if self._settings.model_api_key is None:
            raise NoModelKeyError(
                "No model key is set. Set POC_MODEL_API_KEY and restart the backend."
            )
        in_use = self._take(conversation_id, started=False)
        try:
            client = self._started_client()
            with self._sdk_errors():
                metadata = await client.get_session_metadata(conversation_id)
        except BaseException:
            self._free(conversation_id, in_use)
            raise
        if metadata is None:
            self._free(conversation_id, in_use)
            raise UnknownConversationError("No conversation has this id.")
        return Answer(self, conversation_id, text, in_use)

    async def read_history(self, conversation_id: str) -> list[HistoryMessage]:
        """Returns the messages of a conversation in order.

        When the conversation is answering, waits until it is free, up to the
        wait setting.
        """
        check_conversation_id(conversation_id)
        self._started_client()
        in_use = await self._take_when_free(conversation_id)
        try:
            # The client is taken after the wait: the agent may have been
            # stopped meanwhile.
            client = self._started_client()
            session = await self._resume(client, conversation_id)
            try:
                with self._sdk_errors():
                    events = await session.get_events()
            finally:
                await self._disconnect(session)
        finally:
            self._free(conversation_id, in_use)
        return _history_from(events)

    async def _produce_pieces(
        self, conversation_id: str, text: str, in_use: _ConversationInUse
    ) -> AsyncGenerator[str]:
        if self._in_use.get(conversation_id) is not in_use:
            # Step two came so late that the conversation was given free.
            raise AnswerTimedOutError("The answer was not read in time.")
        try:
            client = self._started_client()
        except AgentError:
            self._free(conversation_id, in_use)
            raise
        in_use.started = True
        session: CopilotSession | None = None
        events: asyncio.Queue[SessionEvent | None] = asyncio.Queue()
        sent = False
        finished = False
        self._open_answers.add(events)
        try:
            session = await self._resume(client, conversation_id)
            loop = asyncio.get_running_loop()

            def receive(event: SessionEvent) -> None:
                # The runtime may call this from another thread, so the event
                # is handed to the event loop instead of put in the queue here.
                loop.call_soon_threadsafe(events.put_nowait, event)

            with self._sdk_errors():
                session.on(receive)
                await session.send(text)
            sent = True
            while True:
                event = await self._next_event(events)
                if event.type is SessionEventType.ASSISTANT_MESSAGE_DELTA:
                    yield cast(AssistantMessageDeltaData, event.data).delta_content
                elif event.type is SessionEventType.SESSION_ERROR:
                    raise self._provider_error(cast(SessionErrorData, event.data))
                elif event.type is SessionEventType.SESSION_IDLE:
                    finished = True
                    return
        finally:
            self._open_answers.discard(events)
            # The clean-up runs as its own task and is shielded, because a
            # browser that leaves a streaming response cancels the task that
            # reads the answer, and may cancel it again at every wait. The
            # clean-up must still stop the model and free the conversation.
            clean_up = asyncio.ensure_future(
                self._clean_up(
                    client,
                    conversation_id,
                    in_use,
                    session,
                    events,
                    sent and not finished,
                )
            )
            self._clean_ups.add(clean_up)
            clean_up.add_done_callback(self._clean_up_done)
            await asyncio.shield(clean_up)

    def _clean_up_done(self, clean_up: asyncio.Task[None]) -> None:
        self._clean_ups.discard(clean_up)
        # When the reader was cancelled, nobody else reads the error of the
        # clean-up. Its text has the key removed already.
        if not clean_up.cancelled() and (error := clean_up.exception()) is not None:
            logger.warning("The clean-up of an answer failed: %s", error)

    async def _clean_up(
        self,
        client: CopilotClient,
        conversation_id: str,
        in_use: _ConversationInUse,
        session: CopilotSession | None,
        events: asyncio.Queue[SessionEvent | None],
        still_answering: bool,
    ) -> None:
        try:
            if session is not None:
                try:
                    # When the agent has stopped, its runtime has ended the
                    # model's request already, and there is nothing to stop.
                    if still_answering and self._client is client:
                        await self._stop_answer(session, events)
                finally:
                    await self._disconnect(session)
        finally:
            self._free(conversation_id, in_use)

    async def _stop_answer(
        self, session: CopilotSession, events: asyncio.Queue[SessionEvent | None]
    ) -> None:
        wait = self._settings.answer_wait_seconds
        with self._sdk_errors():
            try:
                await asyncio.wait_for(session.abort(), wait)
            except TimeoutError:
                raise AgentError(
                    f"The runtime did not stop the model within {wait:g} seconds."
                ) from None
        # The runtime ends a stopped turn with "session.idle". Waiting for it
        # means the next resume finds the session at rest. If it does not
        # come, the session is disconnected all the same.
        with contextlib.suppress(TimeoutError):
            async with asyncio.timeout(wait):
                while True:
                    event = await events.get()
                    if event is None or event.type is SessionEventType.SESSION_IDLE:
                        return

    async def _disconnect(self, session: CopilotSession) -> None:
        wait = self._settings.answer_wait_seconds
        with self._sdk_errors():
            try:
                await asyncio.wait_for(session.disconnect(), wait)
            except TimeoutError:
                raise AgentError(
                    f"The runtime did not disconnect the session within {wait:g} "
                    "seconds."
                ) from None

    async def _next_event(
        self, events: asyncio.Queue[SessionEvent | None]
    ) -> SessionEvent:
        try:
            event = await asyncio.wait_for(
                events.get(), self._settings.answer_wait_seconds
            )
        except TimeoutError:
            raise AnswerTimedOutError(
                "The model sent nothing for "
                f"{self._settings.answer_wait_seconds:g} seconds."
            ) from None
        if event is None:
            raise AgentError("The agent was stopped while the answer was open.")
        return event

    async def _resume(
        self, client: CopilotClient, conversation_id: str
    ) -> CopilotSession:
        self._check_still_held(client)
        with self._sdk_errors():
            metadata = await client.get_session_metadata(conversation_id)
        if metadata is None:
            raise UnknownConversationError("No conversation has this id.")
        self._check_still_held(client)
        with self._sdk_errors():
            # The provider settings and the key are given again on every
            # resume, because the runtime does not store the key on disk.
            return await client.resume_session(
                conversation_id,
                model=self._settings.model_name,
                system_message=self._system_message(),
                permissions=self._permissions(),
                inference=self._inference(),
                tools=self._tools(),
                github=self._github(),
                events=self._events(),
            )

    def _started_client(self) -> CopilotClient:
        if self._client is None:
            raise AgentError("The agent runtime is not started.")
        return self._client

    def _check_still_held(self, client: CopilotClient) -> None:
        # Called right before a call on the SDK's client, with no wait in
        # between. A stopped SDK client starts a new runtime by itself when
        # it is called, and nothing would ever stop that runtime.
        if self._client is not client:
            raise AgentError("The agent runtime is not started.")

    def _take(self, conversation_id: str, started: bool) -> _ConversationInUse:
        current = self._in_use.get(conversation_id)
        if current is not None:
            if not self._abandoned(current):
                raise ConversationBusyError(
                    "The conversation is still answering a message. Wait until "
                    "the answer has ended."
                )
            self._free(conversation_id, current)
        in_use = _ConversationInUse(taken_at=time.monotonic(), started=started)
        self._in_use[conversation_id] = in_use
        return in_use

    async def _take_when_free(self, conversation_id: str) -> _ConversationInUse:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._settings.answer_wait_seconds
        while True:
            current = self._in_use.get(conversation_id)
            if current is None or self._abandoned(current):
                return self._take(conversation_id, started=True)
            try:
                await asyncio.wait_for(current.freed.wait(), deadline - loop.time())
            except TimeoutError:
                raise ConversationBusyError(
                    "The conversation stayed busy for longer than the wait setting."
                ) from None

    def _abandoned(self, in_use: _ConversationInUse) -> bool:
        # An answer whose step two never started, for example because the
        # caller failed between the two steps, must not block the
        # conversation for ever.
        waited = time.monotonic() - in_use.taken_at
        return not in_use.started and waited > self._settings.answer_wait_seconds

    def _free(self, conversation_id: str, in_use: _ConversationInUse) -> None:
        if self._in_use.get(conversation_id) is in_use:
            del self._in_use[conversation_id]
        in_use.freed.set()

    def _provider_error(self, data: SessionErrorData) -> ModelProviderError:
        return ModelProviderError(
            self._without_key(f"The model provider failed: {data.message}"),
            status_code=data.status_code,
        )

    def _without_key(self, text: str) -> str:
        # A provider may repeat the key in an error. The key must never reach
        # an error text, which may be logged or shown.
        key = self._settings.model_api_key
        if key is None or not key.get_secret_value():
            return text
        return text.replace(key.get_secret_value(), "[key removed]")

    @contextlib.contextmanager
    def _sdk_errors(self) -> Iterator[None]:
        # Turns an error of the SDK's runtime into an error of this module.
        try:
            yield
        except SDK_ERRORS as error:
            raise AgentError(
                self._without_key(f"The agent runtime failed: {error}")
            ) from None

    def _system_message(self) -> SystemMessageReplaceConfig:
        # "replace" sends only the project's own prompt, without the
        # runtime's built-in prompt for a coding agent.
        return {"mode": "replace", "content": self._settings.system_prompt}

    def _permissions(self) -> SessionPermissionOptions:
        return {"on_request": _refuse_every_permission}

    def _inference(self) -> SessionInferenceOptions:
        provider: NamedProviderConfig = {
            "name": PROVIDER_LABEL,
            "type": cast(ProviderType, self._settings.model_provider_type),
            "base_url": self._settings.model_provider_address,
        }
        if self._settings.model_api_key is not None:
            provider["api_key"] = self._settings.model_api_key.get_secret_value()
        return {"default_provider": PROVIDER_LABEL, "providers": [provider]}

    def _tools(self) -> SessionToolOptions:
        return {"available_tools": []}

    def _github(self) -> SessionGitHubOptions:
        # Switches off GitHub's own model service, so only the project's
        # provider can answer.
        return {"capi": {"enabled": False}}

    def _events(self) -> SessionEventOptions:
        # Streaming makes the runtime send the answer in pieces.
        return {"streaming": True}


class Answer:
    """Step two of sending a message: the pieces of the answer's text.

    Read it with "async for". It ends when the answer ends. Stopping early,
    by aclose() or by cancelling the task that reads it, stops the model and
    frees the conversation.
    """

    def __init__(
        self,
        agent: Agent,
        conversation_id: str,
        text: str,
        in_use: _ConversationInUse,
    ) -> None:
        self._agent = agent
        self._conversation_id = conversation_id
        self._in_use = in_use
        self._pieces = agent._produce_pieces(conversation_id, text, in_use)

    def __aiter__(self) -> "Answer":
        return self

    async def __anext__(self) -> str:
        return await anext(self._pieces)

    async def aclose(self) -> None:
        if not self._in_use.started:
            # Nothing was sent, so there is nothing to stop.
            self._agent._free(self._conversation_id, self._in_use)
        await self._pieces.aclose()


def _history_from(events: list[SessionEvent]) -> list[HistoryMessage]:
    history: list[HistoryMessage] = []
    for event in events:
        if event.type is SessionEventType.USER_MESSAGE:
            # "content" is the text as the user sent it. The runtime keeps
            # the text with its date line in another field.
            user_text = cast(UserMessageData, event.data).content
            history.append(HistoryMessage(role="user", text=user_text))
        elif event.type is SessionEventType.ASSISTANT_MESSAGE:
            answer_text = cast(AssistantMessageData, event.data).content
            # An answer that was only a request for a tool has no text.
            if answer_text:
                history.append(HistoryMessage(role="assistant", text=answer_text))
    return history
