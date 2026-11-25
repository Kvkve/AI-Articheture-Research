import asyncio
import secrets
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from anyio.from_thread import BlockingPortal
from fastapi.testclient import TestClient
from model_stand_in import ModelStandIn, running_stand_in

from app.agent import Agent
from app.config import get_settings
from app.database import connect, create_tables
from app.main import app
from app.users import create_user

# How long a test waits for the stand-in or the agent to see something. Only
# reached when a test fails, so it does not slow a good run.
STAND_IN_WAIT_SECONDS = 10.0

# Variables that send traffic through a proxy. The runtime honours them, so
# they are removed: the tests must reach the stand-in directly, whatever the
# machine that runs them has set.
PROXY_VARIABLES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


@pytest.fixture(autouse=True)
def database_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Every test gets its own database file in a temporary folder, so no test
    # can write to the default database file. The folder "data" does not
    # exist yet, which also tests that it is made when needed.
    path = tmp_path / "data" / "app.db"
    monkeypatch.setenv("POC_DATABASE_FILE", str(path))
    return path


@pytest.fixture(autouse=True)
def session_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Every test gets its own folder for the SDK's session files, as it gets
    # its own database file, so no test can write to the default folder.
    path = tmp_path / "data" / "sessions"
    monkeypatch.setenv("POC_SESSION_DIRECTORY", str(path))
    return path


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # The application keeps one settings object per process. Clearing it
    # before and after each test gives each test its own settings, read from
    # the environment variables that the test sets. The token and model
    # variables of the machine that runs the tests are removed, so they
    # cannot change a result, and no test can use a real model key.
    for name in (
        "POC_TOKEN_SECRET_KEY",
        "POC_TOKEN_EXPIRE_MINUTES",
        "POC_MODEL_API_KEY",
        "POC_MODEL_NAME",
        "POC_MODEL_PROVIDER_TYPE",
        "POC_MODEL_PROVIDER_ADDRESS",
        "POC_SYSTEM_PROMPT",
        "POC_ANSWER_WAIT_SECONDS",
        "POC_LONGEST_MESSAGE_CHARACTERS",
        "POC_TITLE_CHARACTERS",
    ):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Entering the "with" block runs the application's start-up, which makes
    # the tables.
    with TestClient(app) as test_client:
        yield test_client


@dataclass
class SavedUser:
    id: int
    username: str
    password: str


@pytest.fixture
def add_user(database_file: Path) -> Callable[[str], SavedUser]:
    # Gives the test a function that stores a user with a password made at
    # run time, and returns what the test needs to sign in.
    def add(username: str) -> SavedUser:
        password = secrets.token_urlsafe(16)
        connection = connect(database_file)
        create_tables(connection)
        user_id = create_user(connection, username, password)
        connection.close()
        return SavedUser(id=user_id, username=username.strip(), password=password)

    return add


@pytest.fixture
def sign_in(client: TestClient) -> Callable[[SavedUser], str]:
    # Gives the test a function that signs a user in through the sign-in
    # endpoint and returns the token.
    def get_token(user: SavedUser) -> str:
        response = client.post(
            "/login/access-token",
            data={"username": user.username, "password": user.password},
        )
        assert response.status_code == 200, response.text
        token: str = response.json()["access_token"]
        return token

    return get_token


@pytest.fixture
def stand_in() -> Iterator[ModelStandIn]:
    with running_stand_in() as server:
        yield server


@pytest.fixture
def stand_in_address(monkeypatch: pytest.MonkeyPatch, stand_in: ModelStandIn) -> None:
    # Points the settings at the stand-in, with no key yet.
    for name in PROXY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    monkeypatch.setenv("POC_MODEL_PROVIDER_ADDRESS", stand_in.address)


@pytest.fixture
def model_key(monkeypatch: pytest.MonkeyPatch, stand_in_address: None) -> str:
    # Adds a key made at run time to the settings that point at the stand-in.
    key = secrets.token_urlsafe(24)
    monkeypatch.setenv("POC_MODEL_API_KEY", key)
    return key


def portal_of(client: TestClient) -> BlockingPortal:
    # The test client runs the application on an event loop of its own. The
    # portal lets a test call the agent's async methods on that loop.
    assert client.portal is not None
    return client.portal


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def start_conversation(client: TestClient, token: str) -> dict[str, Any]:
    response = client.post("/conversations", headers=bearer(token))
    assert response.status_code == 201, response.text
    conversation: dict[str, Any] = response.json()
    return conversation


def run_sql(database_file: Path, sql: str, parameters: tuple[Any, ...] = ()) -> None:
    connection = connect(database_file)
    with connection:
        connection.execute(sql, parameters)
    connection.close()


def the_agent() -> Agent:
    # The one agent object that the start-up of the application made.
    agent: Agent = app.state.agent
    return agent


async def wait_until_free(agent: Agent, conversation_id: str) -> None:
    # Reads the agent's private table of busy conversations, because nothing
    # public waits without also opening a session.
    in_use = agent._in_use.get(conversation_id)
    if in_use is not None:
        await asyncio.wait_for(in_use.freed.wait(), STAND_IN_WAIT_SECONDS)
