# What an endpoint can ask for: the settings, a database connection for this
# one request, the signed-in user, and the agent that talks to the model.
# FastAPI calls these functions for each request and passes their results to
# the endpoint.
# get_current_user follows backend/app/api/deps.py in the official FastAPI
# full-stack template (MIT license). See docs/sources.md.
import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.agent import Agent
from app.config import Settings, get_settings
from app.database import connect
from app.security import read_access_token
from app.users import User, get_user_by_id

SettingsDependency = Annotated[Settings, Depends(get_settings)]


class ErrorMessage(BaseModel):
    # The shape of an error answer, for the generated API documentation.
    detail: str


def get_connection(settings: SettingsDependency) -> Iterator[sqlite3.Connection]:
    # FastAPI runs this function, the other dependencies and the endpoint in
    # worker threads, and not always in the same one. sqlite3 refuses by
    # default to use a connection in a thread that did not make it.
    # check_same_thread=False turns that off. It is safe here because the
    # connection belongs to one request, and its steps use it one after the
    # other, never at the same time.
    connection = connect(settings.database_file, check_same_thread=False)
    try:
        yield connection
    finally:
        connection.close()


ConnectionDependency = Annotated[sqlite3.Connection, Depends(get_connection)]

# Reads the header "Authorization: Bearer <token>". With no header, or another
# scheme than Bearer, it answers 401 by itself. tokenUrl is the sign-in
# address, which the "Authorize" button of the page /docs uses.
bearer_token = OAuth2PasswordBearer(tokenUrl="/login/access-token")


def get_current_user(
    token: Annotated[str, Depends(bearer_token)],
    settings: SettingsDependency,
    connection: ConnectionDependency,
) -> User:
    user_id = read_access_token(token, settings.token_secret_key.get_secret_value())
    user = None if user_id is None else get_user_by_id(connection, user_id)
    if user is None:
        # Unlike the template, which answers 403 or 404 here, every failure
        # is 401, so that a frontend reads 401 as "sign in again". The answer
        # is the same for every failure and does not say which check failed.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_agent(request: Request) -> Agent:
    # The start-up step in backend/app/main.py makes the one agent of the
    # process and keeps it on the application.
    agent: Agent = request.app.state.agent
    return agent


AgentDependency = Annotated[Agent, Depends(get_agent)]
