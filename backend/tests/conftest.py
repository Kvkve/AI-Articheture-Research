import secrets
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import connect, create_tables
from app.main import app
from app.users import create_user


@pytest.fixture(autouse=True)
def database_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Every test gets its own database file in a temporary folder, so no test
    # can write to the default database file. The folder "data" does not
    # exist yet, which also tests that it is made when needed.
    path = tmp_path / "data" / "app.db"
    monkeypatch.setenv("POC_DATABASE_FILE", str(path))
    return path


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # The application keeps one settings object per process. Clearing it
    # before and after each test gives each test its own settings, read from
    # the environment variables that the test sets. The token variables of
    # the machine that runs the tests are removed, so they cannot change a
    # result.
    monkeypatch.delenv("POC_TOKEN_SECRET_KEY", raising=False)
    monkeypatch.delenv("POC_TOKEN_EXPIRE_MINUTES", raising=False)
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
