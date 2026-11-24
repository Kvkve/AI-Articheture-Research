import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from conftest import SavedUser
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import LONGEST_TOKEN_EXPIRE_MINUTES, Settings, get_settings
from app.main import app
from app.security import ALGORITHM, create_access_token


def test_with_no_variable_the_key_has_at_least_32_characters() -> None:
    settings = Settings()

    assert len(settings.token_secret_key.get_secret_value()) >= 32


def test_with_no_variable_the_next_request_accepts_the_token(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    # The sign-in and the next request share one key, so the process makes
    # its settings once.
    token = sign_in(add_user("alice"))

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_with_the_variable_set_that_key_is_used(
    monkeypatch: pytest.MonkeyPatch,
    add_user: Callable[[str], SavedUser],
) -> None:
    key = secrets.token_urlsafe(32)
    monkeypatch.setenv("POC_TOKEN_SECRET_KEY", key)
    alice = add_user("alice")
    token = jwt.encode(
        {"sub": str(alice.id), "exp": datetime.now(UTC) + timedelta(hours=1)},
        key,
        algorithm=ALGORITHM,
    )

    with TestClient(app) as client:
        response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"id": alice.id, "username": "alice"}


def test_a_key_shorter_than_32_characters_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    short_key = secrets.token_urlsafe(32)[:31]
    monkeypatch.setenv("POC_TOKEN_SECRET_KEY", short_key)

    with pytest.raises(ValidationError) as error:
        Settings()

    assert "POC_TOKEN_SECRET_KEY" in str(error.value)
    # The refused key must not appear in the error, which may be logged.
    assert short_key not in str(error.value)


@pytest.mark.parametrize("minutes", ["0", "-5"])
def test_a_lifetime_of_zero_or_less_is_refused(
    monkeypatch: pytest.MonkeyPatch, minutes: str
) -> None:
    monkeypatch.setenv("POC_TOKEN_EXPIRE_MINUTES", minutes)

    with pytest.raises(ValidationError):
        Settings()


def test_a_lifetime_above_one_year_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "POC_TOKEN_EXPIRE_MINUTES", str(LONGEST_TOKEN_EXPIRE_MINUTES + 1)
    )

    with pytest.raises(ValidationError):
        Settings()


def test_sign_in_works_with_the_longest_lifetime_allowed(
    monkeypatch: pytest.MonkeyPatch,
    add_user: Callable[[str], SavedUser],
) -> None:
    monkeypatch.setenv("POC_TOKEN_EXPIRE_MINUTES", str(LONGEST_TOKEN_EXPIRE_MINUTES))
    alice = add_user("alice")

    with TestClient(app) as client:
        response = client.post(
            "/login/access-token",
            data={"username": alice.username, "password": alice.password},
        )
        token = response.json()["access_token"]
        me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert me.status_code == 200


def test_create_access_token_sets_the_expiry_from_the_lifetime() -> None:
    key = secrets.token_urlsafe(32)
    made_at = datetime.now(UTC)

    token = create_access_token(7, key, timedelta(minutes=30))

    payload = jwt.decode(token, key, algorithms=[ALGORITHM])
    expected = made_at + timedelta(minutes=30)
    assert abs(payload["exp"] - expected.timestamp()) < 5


def test_sign_in_uses_the_lifetime_from_the_settings(
    monkeypatch: pytest.MonkeyPatch,
    add_user: Callable[[str], SavedUser],
) -> None:
    monkeypatch.setenv("POC_TOKEN_EXPIRE_MINUTES", "45")
    alice = add_user("alice")
    made_at = datetime.now(UTC)

    with TestClient(app) as client:
        response = client.post(
            "/login/access-token",
            data={"username": alice.username, "password": alice.password},
        )

    key = get_settings().token_secret_key.get_secret_value()
    payload = jwt.decode(response.json()["access_token"], key, algorithms=[ALGORITHM])
    expected = made_at + timedelta(minutes=45)
    assert abs(payload["exp"] - expected.timestamp()) < 5


def test_after_a_restart_with_a_new_random_key_an_old_token_is_refused(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    # This is the cost the owner accepted: without POC_TOKEN_SECRET_KEY, a
    # restart signs every user out. Clearing the stored settings stands in
    # for a restart: the next request makes new settings with a new key.
    token = sign_in(add_user("alice"))

    get_settings.cache_clear()
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
