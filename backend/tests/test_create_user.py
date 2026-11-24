import secrets
from collections.abc import Iterator
from pathlib import Path

import pytest

from app import create_user
from app.database import connect


def replace_getpass(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    # The script asks for the password twice; each call gives the next answer.
    remaining: Iterator[str] = iter(answers)
    monkeypatch.setattr(create_user, "getpass", lambda prompt: next(remaining))


def usernames_in(database_file: Path) -> list[str]:
    connection = connect(database_file)
    rows = connection.execute("SELECT username FROM users").fetchall()
    connection.close()
    return [row["username"] for row in rows]


def test_the_script_creates_a_user(
    database_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    password = secrets.token_urlsafe(16)
    replace_getpass(monkeypatch, [password, password])

    exit_code = create_user.main(["alice"])

    assert exit_code == 0
    assert usernames_in(database_file) == ["alice"]
    assert password.encode() not in database_file.read_bytes()
    output = capsys.readouterr()
    assert "alice" in output.out
    assert password not in output.out
    assert password not in output.err


def test_the_script_refuses_a_username_that_exists(
    database_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first_password = secrets.token_urlsafe(16)
    replace_getpass(monkeypatch, [first_password, first_password])
    assert create_user.main(["alice"]) == 0
    capsys.readouterr()

    second_password = secrets.token_urlsafe(16)
    replace_getpass(monkeypatch, [second_password, second_password])
    exit_code = create_user.main(["alice"])

    assert exit_code != 0
    assert "already exists" in capsys.readouterr().err
    assert usernames_in(database_file) == ["alice"]


def test_the_script_refuses_passwords_that_differ(
    database_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    replace_getpass(monkeypatch, [secrets.token_urlsafe(16), secrets.token_urlsafe(16)])

    exit_code = create_user.main(["alice"])

    assert exit_code != 0
    assert "differ" in capsys.readouterr().err
    assert not database_file.exists() or usernames_in(database_file) == []
