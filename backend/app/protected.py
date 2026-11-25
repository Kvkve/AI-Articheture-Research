# Every endpoint that needs a token goes on this router. The router asks for
# the signed-in user before any of its endpoints runs, so an endpoint added
# here cannot forget the token.
#
# The two endpoints that call the agent are "async def", because the actions
# of the agent are async. Their database calls then run on the event loop and
# block it for a moment. This is accepted for the first PoC: the calls are
# short and the database is a local file. An endpoint that does not call the
# agent is a plain "def", which FastAPI runs in a worker thread.
import logging
import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.conversations import (
    Conversation,
    create_conversation,
    find_conversation,
    list_conversations,
)
from app.dependencies import (
    AgentDependency,
    ConnectionDependency,
    CurrentUser,
    ErrorMessage,
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
