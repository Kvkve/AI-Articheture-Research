# Every endpoint that needs a token goes on this router. The router asks for
# the signed-in user before any of its endpoints runs, so an endpoint added
# here cannot forget the token.
#
# The endpoints that call the agent are "async def", because the actions of
# the agent are async. Their database calls then run on the event loop and
# block it for a moment. This is accepted for the first PoC: the calls are
# short and the database is a local file. An endpoint that does not call the
# agent is a plain "def", which FastAPI runs in a worker thread.
import logging
import sqlite3
from collections.abc import AsyncIterable, AsyncIterator
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel, Field

from app.agent import AgentError, Answer, ModelProviderError
from app.agent_errors import ANSWER_FAILED_TEXT
from app.conversations import (
    Conversation,
    create_conversation,
    find_conversation,
    list_conversations,
    make_title,
    record_message,
)
from app.dependencies import (
    AgentDependency,
    ConnectionDependency,
    CurrentUser,
    ErrorMessage,
    SettingsDependency,
    get_current_user,
)
from app.users import User

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(get_current_user)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorMessage,
            "description": "No token, or the token is not valid. Sign in again.",
        },
    },
)

# The answers are objects with one list inside, not bare lists, so that a
# field can be added later without breaking a frontend.


class ConversationList(BaseModel):
    conversations: list[Conversation]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class MessageList(BaseModel):
    messages: list[Message]


NOT_FOUND_TEXT = "Conversation not found"
NOT_STORED_TEXT = "The conversation could not be started. Try again later."

NOT_FOUND_ANSWER = {
    "model": ErrorMessage,
    "description": (
        "The signed-in user has no conversation with this id. The answer is "
        "the same whether the conversation belongs to another user or does "
        "not exist."
    ),
}
BUSY_ANSWER = {
    "model": ErrorMessage,
    "description": (
        "The conversation is still answering a message after the longest "
        "wait. Try again later."
    ),
}
# The cause of a failure is in the log of the backend, not in the answer.
AGENT_FAILED_ANSWER = {
    "model": ErrorMessage,
    "description": "The agent module failed.",
}
NOT_STARTED_ANSWER = {
    "model": ErrorMessage,
    "description": (
        "The agent module failed, or the row of the new conversation could "
        "not be stored."
    ),
}


@router.get(
    "/users/me",
    tags=["users"],
    summary="Get the signed-in user",
)
def read_current_user(user: CurrentUser) -> User:
    # FastAPI runs get_current_user once per request, even though both the
    # router and this endpoint ask for it.
    return user


@router.post(
    "/conversations",
    tags=["conversations"],
    summary="Start a conversation",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: NOT_STARTED_ANSWER},
)
async def start_conversation(
    user: CurrentUser, connection: ConnectionDependency, agent: AgentDependency
) -> Conversation:
    # The agent makes the session first, and its id becomes the key of the
    # row. The other order would leave a row that the user sees in the list
    # and cannot open.
    conversation_id = await agent.start_conversation()
    try:
        return create_conversation(connection, conversation_id, user.id)
    except sqlite3.Error:
        # The session stays on disk. No row names it, so no user can reach
        # it, and nothing cleans it up. The log names it for a person.
        logger.exception(
            "The row of conversation %s could not be stored. Its session "
            "stays on disk with no row.",
            conversation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=NOT_STORED_TEXT,
        ) from None


@router.get(
    "/conversations",
    tags=["conversations"],
    summary="List the signed-in user's conversations",
    description="The latest activity first.",
)
def read_conversations(
    user: CurrentUser, connection: ConnectionDependency
) -> ConversationList:
    return ConversationList(conversations=list_conversations(connection, user.id))


@router.get(
    "/conversations/{conversation_id}/messages",
    tags=["conversations"],
    summary="Read the history of a conversation",
    responses={
        status.HTTP_404_NOT_FOUND: NOT_FOUND_ANSWER,
        status.HTTP_409_CONFLICT: BUSY_ANSWER,
        status.HTTP_500_INTERNAL_SERVER_ERROR: AGENT_FAILED_ANSWER,
    },
)
async def read_messages(
    conversation_id: str,
    user: CurrentUser,
    connection: ConnectionDependency,
    agent: AgentDependency,
) -> MessageList:
    # The table of conversations says who owns each one. The agent is asked
    # only after this check, so a request for a conversation of another user
    # never reaches the session files.
    if find_conversation(connection, conversation_id, user.id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_TEXT
        )
    history = await agent.read_history(conversation_id)
    return MessageList(
        messages=[Message(role=message.role, text=message.text) for message in history]
    )


# Sending a message. The request body, the messages of the stream and the
# error answers below are a contract for every frontend, so each part has a
# description that the generated API documentation shows.


class NewMessage(BaseModel):
    """The message that the signed-in user sends."""

    text: str = Field(
        description=(
            "The text of the message, as the user wrote it. It must not be "
            "empty or hold only white space, and it must not be longer than "
            "the backend's setting for the longest message. The length is "
            "counted in characters, as Unicode code points. The first message "
            "of a conversation also gives the conversation its title."
        )
    )


# Each kind of message of the stream has a "type" field with no default, so
# that the generated documentation marks it as always present.


class StreamText(BaseModel):
    """One piece of the answer's text. The pieces come in order, each as soon
    as the model has written it. Joined in order, they give the answer's
    text."""

    type: Literal["text"] = Field(description='Always "text".')
    text: str = Field(description="The piece of text. It may hold line breaks.")


class StreamEnd(BaseModel):
    """The answer is complete. It is the last message of the stream."""

    type: Literal["end"] = Field(description='Always "end".')


class StreamError(BaseModel):
    """The answer could not be completed. It is the last message of the
    stream. The pieces of text before it are only part of the answer."""

    type: Literal["error"] = Field(description='Always "error".')
    message: str = Field(
        description=(
            "A general text for the user. The cause is in the log of the backend only."
        )
    )


StreamMessage = Annotated[
    StreamText | StreamEnd | StreamError, Field(discriminator="type")
]

SEND_MESSAGE_DESCRIPTION = """\
Sends a message to a conversation of the signed-in user, and streams the
answer back as Server-Sent Events.

The steps, in order. A refusal in any step is an ordinary JSON answer with
its status code, and never a stream:

1. The token is checked: 401.
2. The body is checked: 422 when the text is missing, empty, only white
   space, or longer than the setting for the longest message. Nothing reaches
   the model.
3. The conversation must be the signed-in user's own: 404.
4. The agent takes the message: 409 when the conversation is still busy, 503
   when the backend has no model key, 500 for any other failure.
5. The time of the last activity of the conversation is set to now. When the
   conversation has no title yet, the opening of this message becomes its
   title.
6. The stream starts, with status 200.

The stream. Each message is one line that begins with "data:" and holds one
JSON object, followed by an empty line. The field "type" of the object gives
the kind of message: "text", "end" or "error". The "event:" line of
Server-Sent Events is not used.

A stream ends with exactly one "end" message or one "error" message, and no
message follows it. No "end" follows an "error". A stream that closes with
neither was cut off.

A line that begins with a colon, such as ": ping", is a comment. The backend
sends one when the stream has been quiet for a while. A reader skips it.

A reader that closes the connection before the end stops the answer: the
model is stopped and the conversation is freed for a new message.

After a stream that was cut off, read the history of the conversation to see
what was stored, before sending the message again.

The EventSource of a browser cannot make this request, because it cannot send
a POST, a body or a token. A frontend reads the stream with fetch, or with
any other client that gives the answer as it arrives.
"""


def json_error_answer(model: type[BaseModel], description: str) -> dict[str, Any]:
    # With "model", FastAPI would document an error answer under the media
    # type of the stream. These answers are JSON, so the content is given here.
    return {
        "description": description,
        "content": {"application/json": {"schema": model.model_json_schema()}},
    }


def refuse_text(
    error_type: str, message: str, context: dict[str, int] | None = None
) -> RequestValidationError:
    # The same shape as the 422 that FastAPI gives for a body that fails
    # validation, so that a frontend has one rule for every 422. There is no
    # "input" field: the answer must not repeat a text that is too long.
    entry: dict[str, Any] = {
        "type": error_type,
        "loc": ("body", "text"),
        "msg": message,
    }
    if context is not None:
        # "ctx" is where FastAPI's own entries carry numbers such as a limit,
        # so a frontend can read the limit without reading the sentence.
        entry["ctx"] = context
    return RequestValidationError([entry])


async def begin_sending(
    conversation_id: str,
    message: NewMessage,
    user: CurrentUser,
    connection: ConnectionDependency,
    agent: AgentDependency,
    settings: SettingsDependency,
) -> AsyncIterator[Answer]:
    # Every step that can refuse the message runs here, in a dependency,
    # because a dependency runs before the status 200 of the stream goes
    # out. An error raised here becomes an answer with its own status code.
    # The code of the endpoint itself runs only after the 200 has gone out.
    if not message.text.strip():
        raise refuse_text(
            "value_error", "The message is empty or holds only white space."
        )
    longest = settings.longest_message_characters
    if len(message.text) > longest:
        raise refuse_text(
            "string_too_long",
            f"The message is longer than {longest} characters.",
            {"max_length": longest},
        )
    if find_conversation(connection, conversation_id, user.id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_TEXT
        )
    # Errors of the agent rise to the handlers in backend/app/agent_errors.py.
    answer = await agent.begin_answer(conversation_id, message.text)
    try:
        # After step one of the agent, so that a refused message changes
        # neither the title nor the time.
        record_message(
            connection,
            conversation_id,
            make_title(message.text, settings.title_characters),
        )
        yield answer
    finally:
        # Runs after the stream has ended, when the reader has gone away, and
        # when the write above fails. An answer that is not closed would keep
        # the conversation busy.
        await answer.aclose()


@router.post(
    "/conversations/{conversation_id}/messages",
    tags=["conversations"],
    summary="Send a message and stream the answer",
    description=SEND_MESSAGE_DESCRIPTION,
    response_class=EventSourceResponse,
    response_description=(
        "The stream of the answer. Each message is one of three kinds, told "
        'apart by the field "type".'
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: json_error_answer(
            ErrorMessage, "No token, or the token is not valid. Sign in again."
        ),
        status.HTTP_404_NOT_FOUND: json_error_answer(
            ErrorMessage,
            "The signed-in user has no conversation with this id. The answer is "
            "the same whether the conversation belongs to another user or does "
            "not exist.",
        ),
        status.HTTP_409_CONFLICT: json_error_answer(
            ErrorMessage,
            "The conversation is still answering an earlier message, or its "
            "history is being read at this moment. Nothing of this message "
            "reaches the model. Try again later.",
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: json_error_answer(
            ErrorMessage,
            "The agent module failed before the stream started. The body holds "
            "a general text. A failure of the database before the stream "
            "starts gives a plain-text answer instead, not JSON.",
        ),
        status.HTTP_503_SERVICE_UNAVAILABLE: json_error_answer(
            ErrorMessage,
            "The backend has no model key, so it cannot answer messages.",
        ),
    },
    # FastAPI adds the 422 answer with its schema by itself. This only gives
    # it a description.
    openapi_extra={
        "responses": {
            "422": {
                "description": (
                    "The body is not valid: the text is missing or not a "
                    "string, empty, only white space, or longer than the "
                    "setting for the longest message. Each entry of the list "
                    'under "detail" names the field in "loc" and the problem '
                    'in "msg". The answer for a text that is too long does '
                    "not repeat the text, and gives the limit as the number "
                    '"max_length" under "ctx".'
                )
            }
        }
    },
)
async def send_message(
    conversation_id: str,
    answer: Annotated[Answer, Depends(begin_sending)],
) -> AsyncIterable[StreamMessage]:
    try:
        async for piece in answer:
            yield StreamText(type="text", text=piece)
    except AgentError as error:
        # Only an error of the agent module becomes an error message. Any
        # other error is a fault of the backend's own code and must not be
        # hidden. The cause goes to the log only, as for the error answers.
        status_code = (
            error.status_code if isinstance(error, ModelProviderError) else None
        )
        logger.error(
            "The answer in conversation %s failed: %s: %s (provider status: %s)",
            conversation_id,
            type(error).__name__,
            error,
            status_code,
        )
        yield StreamError(type="error", message=ANSWER_FAILED_TEXT)
        return
    yield StreamEnd(type="end")
