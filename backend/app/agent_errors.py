# The one place that turns an error of the agent module into an answer with a
# status code. The endpoints let these errors rise, and the handlers below
# answer them. The answer has the same JSON shape as every other error,
# {"detail": "..."}, with a fixed, general text. The text of the error itself
# goes to the log of the backend only, because it can name inner details
# that the browser must not see.
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.agent import AgentError, ConversationBusyError

logger = logging.getLogger(__name__)

BUSY_TEXT = "The conversation is still answering a message. Try again later."
FAILED_TEXT = "The agent could not do this. Try again later."


async def answer_conversation_busy(request: Request, error: Exception) -> JSONResponse:
    # A busy conversation is a normal state, not a fault of the backend.
    logger.warning("%s %s: %s", request.method, request.url.path, error)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": BUSY_TEXT}
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
    # ConversationBusyError gets 409, and every other AgentError gets 500.
    app.add_exception_handler(ConversationBusyError, answer_conversation_busy)
    app.add_exception_handler(AgentError, answer_agent_failed)
