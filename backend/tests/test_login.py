import secrets
from collections.abc import Callable
from pathlib import Path

import pytest
from conftest import SavedUser
from fastapi.testclient import TestClient

from app import users
from app.database import connect, create_tables


def test_a_right_name_and_password_give_a_token_that_names_the_user(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
) -> None:
    alice = add_user("alice")

    response = client.post(
        "/login/access-token",
        data={"username": alice.username, "password": alice.password},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"access_token": body["access_token"], "token_type": "bearer"}
    me = client.get(
        "/users/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json() == {"id": alice.id, "username": "alice"}


def test_each_token_names_its_own_user(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    alice = add_user("alice")
    bob = add_user("bob")
    alice_token = sign_in(alice)
    bob_token = sign_in(bob)

    alice_me = client.get(
        "/users/me", headers={"Authorization": f"Bearer {alice_token}"}
    )
    bob_me = client.get("/users/me", headers={"Authorization": f"Bearer {bob_token}"})

    assert alice_me.json() == {"id": alice.id, "username": "alice"}
    assert bob_me.json() == {"id": bob.id, "username": "bob"}


def test_a_wrong_password_and_an_unknown_name_give_the_same_400(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
) -> None:
    alice = add_user("alice")

    wrong_password = client.post(
        "/login/access-token",
        data={"username": alice.username, "password": secrets.token_urlsafe(16)},
    )
    unknown_name = client.post(
        "/login/access-token",
        data={"username": "nobody", "password": secrets.token_urlsafe(16)},
    )

    assert wrong_password.status_code == 400
    assert unknown_name.status_code == 400
    assert wrong_password.json() == unknown_name.json()
    assert "access_token" not in wrong_password.json()


def test_a_name_with_white_space_around_it_signs_in(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
) -> None:
    alice = add_user("alice")

    response = client.post(
        "/login/access-token",
        data={"username": "  alice  ", "password": alice.password},
    )

    assert response.status_code == 200


def test_an_unknown_name_still_runs_a_password_check(
    database_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked_hashes: list[str] = []

    def record_check(password: str, password_hash: str) -> bool:
        checked_hashes.append(password_hash)
        return False

    monkeypatch.setattr(users, "verify_password", record_check)
    connection = connect(database_file)
    create_tables(connection)

    user = users.authenticate(connection, "nobody", secrets.token_urlsafe(16))

    connection.close()
    assert user is None
    assert checked_hashes == [users.DUMMY_HASH]


def test_no_answer_holds_the_password_or_its_hash(
    client: TestClient,
    database_file: Path,
    add_user: Callable[[str], SavedUser],
) -> None:
    alice = add_user("alice")
    connection = connect(database_file)
    stored_hash = connection.execute(
        "SELECT password_hash FROM users WHERE id = ?", (alice.id,)
    ).fetchone()["password_hash"]
    connection.close()

    good_sign_in = client.post(
        "/login/access-token",
        data={"username": alice.username, "password": alice.password},
    )
    bad_sign_in = client.post(
        "/login/access-token",
        data={"username": alice.username, "password": alice.password + "x"},
    )
    token = good_sign_in.json()["access_token"]
    me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    for response in (good_sign_in, bad_sign_in, me):
        assert alice.password not in response.text
        assert stored_hash not in response.text


def test_the_api_documentation_describes_sign_in(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    sign_in = schema["paths"]["/login/access-token"]["post"]
    me = schema["paths"]["/users/me"]["get"]
    assert sign_in["summary"]
    assert {"200", "400"} <= set(sign_in["responses"])
    assert me["summary"]
    assert {"200", "401"} <= set(me["responses"])
    # The "Authorize" button of the page /docs signs in at this address.
    flows = schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]
    assert flows["password"]["tokenUrl"] == "/login/access-token"
