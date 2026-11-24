from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_fails_on_purpose_to_show_that_the_checks_catch_it() -> None:
    assert 1 + 1 == 3
