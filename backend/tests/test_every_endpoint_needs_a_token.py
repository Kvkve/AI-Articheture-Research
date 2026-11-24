import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import jwt
from conftest import SavedUser
from fastapi.routing import iter_route_contexts
from fastapi.testclient import TestClient

from app.main import app
from app.security import ALGORITHM

# The method and path of each endpoint that answers without a token. Every
# other endpoint of the application must refuse a request that has no valid
# token. This list is the one place that makes an exception, so a new
# endpoint, or a new method on an open path, cannot be left open by mistake.
# Add a pair to this list only when the owner agrees.
# The test tries routes only. It does not see a request that is answered
# before it reaches the routes, for example by a middleware.
OPEN_ENDPOINTS = {
    ("GET", "/health"),
    ("POST", "/login/access-token"),
    # The pages of the generated API documentation, which FastAPI adds.
    ("GET", "/openapi.json"),
    ("HEAD", "/openapi.json"),
    ("GET", "/docs"),
    ("HEAD", "/docs"),
    ("GET", "/docs/oauth2-redirect"),
    ("HEAD", "/docs/oauth2-redirect"),
    ("GET", "/redoc"),
    ("HEAD", "/redoc"),
}


def test_every_endpoint_outside_the_open_list_needs_a_token(
    client: TestClient,
    add_user: Callable[[str], SavedUser],
) -> None:
    # A made-up text that is not a token. An endpoint that only looks for the
    # header, and never checks the token in it, would answer this request.
    not_a_token = secrets.token_urlsafe(32)
    # A token of the right form for a user that exists, signed with a key that
    # is not the application's. An endpoint that reads the token and does not
    # check the signature would answer this request.
    alice = add_user("alice")
    forged_token = jwt.encode(
        {"sub": str(alice.id), "exp": datetime.now(UTC) + timedelta(hours=1)},
        secrets.token_urlsafe(32),
        algorithm=ALGORITHM,
    )
    requests_to_refuse = {
        "with no token": {},
        "whose token is a made-up text": {"Authorization": f"Bearer {not_a_token}"},
        "whose token is signed with another key": {
            "Authorization": f"Bearer {forged_token}"
        },
    }
    tried_endpoints = set()
    # app.routes holds each included router as one entry, not its endpoints.
    # iter_route_contexts goes into those routers and gives every endpoint.
    for route in iter_route_contexts(app.routes):
        # A route that this test cannot try must fail the test. If it were
        # skipped, it could be open and nobody would see.
        assert route.path is not None, f"{route} has no path, so it cannot be tried"
        assert route.methods, f"{route.path} has no methods, so it cannot be tried"
        for method in sorted(route.methods):
            if (method, route.path) in OPEN_ENDPOINTS:
                continue
            for what, headers in requests_to_refuse.items():
                response = client.request(method, route.path, headers=headers)
                assert response.status_code == 401, (
                    f"{method} {route.path} answers a request {what}"
                )
            tried_endpoints.add((method, route.path))

    # Without this, the test would pass if it tried nothing.
    assert ("GET", "/users/me") in tried_endpoints
