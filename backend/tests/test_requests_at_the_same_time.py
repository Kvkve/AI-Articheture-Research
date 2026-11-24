import asyncio
from collections.abc import Callable

import httpx2
from conftest import SavedUser

from app.main import app

NUMBER_OF_REQUESTS = 60


async def send_at_the_same_time(token: str) -> list[httpx2.Response]:
    # raise_app_exceptions=False turns an error inside the application into a
    # 500 answer, as a real server does, instead of an exception in the test.
    transport = httpx2.ASGITransport(app=app, raise_app_exceptions=False)
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx2.AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        return await asyncio.gather(
            *(
                client.get("/users/me", headers=headers)
                for _ in range(NUMBER_OF_REQUESTS)
            )
        )


def test_many_requests_at_the_same_time_each_name_the_right_user(
    add_user: Callable[[str], SavedUser],
    sign_in: Callable[[SavedUser], str],
) -> None:
    # Protects check_same_thread=False in get_connection of
    # backend/app/dependencies.py. When requests overlap, FastAPI runs the
    # steps of one request in different worker threads, and sqlite3 then
    # refuses the connection unless that setting is there. The other tests
    # send one request after another, so they would not notice.
    # This client does not run the application's start-up; add_user makes
    # the tables. Sign-in happens once, because hashing a password is slow.
    alice = add_user("alice")
    token = sign_in(alice)

    responses = asyncio.run(send_at_the_same_time(token))

    status_codes = [response.status_code for response in responses]
    assert status_codes == [200] * NUMBER_OF_REQUESTS
    for response in responses:
        assert response.json() == {"id": alice.id, "username": "alice"}
