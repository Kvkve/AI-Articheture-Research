import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from conftest import SavedUser
from fastapi.testclient import TestClient

from app.config import get_settings
from app.security import ALGORITHM


def the_secret_key() -> str:
    return get_settings().token_secret_key.get_secret_value()


def make_token(payload: dict[str, Any], key: str | None = None) -> str:
    # Signs a token by hand, so a test can make tokens that sign-in never gives.
    return jwt.encode(payload, key or the_secret_key(), algorithm=ALGORITHM)


def in_one_hour() -> datetime:
    return datetime.now(UTC) + timedelta(hours=1)


def change_one_character(token: str) -> str:
    # The first character of the signature part. Changing it changes the
    # signature's first byte; the last character might only change unused bits.
    position = token.rindex(".") + 1
    new_character = "B" if token[position] == "A" else "A"
    return token[:position] + new_character + token[position + 1 :]


def assert_refused(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    body: dict[str, Any] = response.json()
    return body


def test_no_token_is_refused(client: TestClient) -> None:
    assert_refused(client, {})


def test_another_scheme_than_bearer_is_refused(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    token = sign_in(add_user("alice"))

    assert_refused(client, {"Authorization": f"Basic {token}"})


def test_a_token_with_one_character_changed_is_refused(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    token = sign_in(add_user("alice"))

    assert_refused(client, {"Authorization": f"Bearer {change_one_character(token)}"})


# Each case gives the payload of a token signed with the application's key,
# except where a case signs with another key or with no key.
def bad_token_for(case: str, user_id: int) -> str:
    sub = str(user_id)
    if case == "signed with another key":
        return make_token({"sub": sub, "exp": in_one_hour()}, secrets.token_urlsafe(32))
    if case == "expired":
        expired = datetime.now(UTC) - timedelta(minutes=1)
        return make_token({"sub": sub, "exp": expired})
    if case == "algorithm none":
        return jwt.encode({"sub": sub, "exp": in_one_hour()}, None, algorithm="none")
    if case == "no exp":
        return make_token({"sub": sub})
    if case == "no sub":
        return make_token({"exp": in_one_hour()})
    if case == "sub is not a whole number":
        return make_token({"sub": "alice", "exp": in_one_hour()})
    if case == "user id not in the table":
        return make_token({"sub": str(user_id + 1000), "exp": in_one_hour()})
    if case == "user id too large for SQLite":
        return make_token({"sub": "9" * 30, "exp": in_one_hour()})
    raise ValueError(case)


BAD_TOKEN_CASES = [
    "signed with another key",
    "expired",
    "algorithm none",
    "no exp",
    "no sub",
    "sub is not a whole number",
    "user id not in the table",
    "user id too large for SQLite",
]


@pytest.mark.parametrize("case", BAD_TOKEN_CASES)
def test_a_token_that_is_not_valid_is_refused(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    case: str,
) -> None:
    alice = add_user("alice")
    token = bad_token_for(case, alice.id)

    assert_refused(client, {"Authorization": f"Bearer {token}"})


def test_every_token_that_is_not_valid_gets_the_same_answer(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    alice = add_user("alice")
    tokens = [bad_token_for(case, alice.id) for case in BAD_TOKEN_CASES]
    tokens.append(change_one_character(sign_in(alice)))

    bodies = [
        assert_refused(client, {"Authorization": f"Bearer {token}"}) for token in tokens
    ]

    assert all(body == bodies[0] for body in bodies)


def test_a_token_the_test_signs_with_the_right_key_is_accepted(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
) -> None:
    # Shows that the tokens above are refused for the one fault each has,
    # not because hand-made tokens are refused in general.
    alice = add_user("alice")
    token = make_token({"sub": str(alice.id), "exp": in_one_hour()})

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"id": alice.id, "username": "alice"}
