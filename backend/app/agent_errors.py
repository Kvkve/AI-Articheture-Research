# The one place that holds what a browser is told about an error of the
# agent module. The endpoints let these errors rise, and the handlers below
# answer them. The answer has the same JSON shape as every other error,
# {"detail": "..."}, with a fixed text. The text of the error itself goes to
# the log of the backend only, because it can name inner details that the
# browser must not see.
#
# An error that comes while an answer streams cannot change the status code
# any more, which has gone out with the start of the stream. The endpoint in
# backend/app/protected.py then ends the stream with an error message that
# holds ANSWER_FAILED_TEXT.
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.agent import AgentError, ConversationBusyError, NoModelKeyError

logger = logging.getLogger(__name__)

BUSY_TEXT = "The conversation is still answering a message. Try again later."
FAILED_TEXT = "The agent could not do this. Try again later."
NO_MODEL_KEY_TEXT = (
    "The backend has no model key, so it cannot answer messages. "
    "The person who runs the backend must set one."
)
ANSWER_FAILED_TEXT = "The answer could not be completed. Try again later."


async def answer_conversation_busy(request: Request, error: Exception) -> JSONResponse:
    # A busy conversation is a normal state, not a fault of the backend.
    logger.warning("%s %s: %s", request.method, request.url.path, error)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": BUSY_TEXT}
    )


async def answer_no_model_key(request: Request, error: Exception) -> JSONResponse:
    # The owner chose a text of its own for this, so that the interface can
    # show the cause. It is a fault of the set-up, so it is logged as an error.
    logger.error(
        "%s %s: %s: %s",
        request.method,
        request.url.path,
        type(error).__name__,
        error,
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": NO_MODEL_KEY_TEXT},
    )


async def answer_agent_failed(request: Request, error: Exception) -> JSONResponse:
    # Every other error of the module, such as session files that are gone
    # for a stored row, or a runtime that failed, is a fault of the backend.
    logger.error(
        "%s %s: %s: %s",
        request.method,
        request.url.path,
        type(error).__name__,
        error,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": FAILED_TEXT},
    )


def add_agent_error_handlers(app: FastAPI) -> None:
    # For each error, the application uses the handler of its own class when
    # there is one, and otherwise the handler of the nearest base class. So
    # ConversationBusyError gets 409, NoModelKeyError gets 503, and every
    # other AgentError gets 500.
    app.add_exception_handler(ConversationBusyError, answer_conversation_busy)
    app.add_exception_handler(NoModelKeyError, answer_no_model_key)
    app.add_exception_handler(AgentError, answer_agent_failed)
