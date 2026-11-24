from fastapi.routing import iter_route_contexts
from fastapi.testclient import TestClient

from app.main import app

# The endpoints that answer without a token. Every other endpoint of the
# application must refuse a request that has no token. This list is the one
# place that makes an exception, so a new endpoint cannot be left open by
# mistake. Add an endpoint to this list only when the owner agrees.
OPEN_PATHS = {
    "/health",
    "/login/access-token",
    # The pages of the generated API documentation, which FastAPI adds.
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
}


def test_every_endpoint_outside_the_open_list_needs_a_token(client: TestClient) -> None:
    tried_paths = set()
    # app.routes holds each included router as one entry, not its endpoints.
    # iter_route_contexts goes into those routers and gives every endpoint.
    for route in iter_route_contexts(app.routes):
        # A route that this test cannot try must fail the test. If it were
        # skipped, it could be open and nobody would see.
        assert route.path is not None, f"{route} has no path, so it cannot be tried"
        if route.path in OPEN_PATHS:
            continue
        assert route.methods, f"{route.path} has no methods, so it cannot be tried"
        for method in sorted(route.methods):
            response = client.request(method, route.path)
            assert response.status_code == 401, f"{method} {route.path} is open"
        tried_paths.add(route.path)

    # Without this, the test would pass if it tried nothing.
    assert "/users/me" in tried_paths
