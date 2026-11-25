# The browser test of the whole product: the page of frontend/, served by
# its development server, which passes the calls on to the real backend
# under uvicorn, which runs the real agent module against the stand-in for
# the model provider. No real model is called.
#
# It is a test of the whole product, but it lives in the backend folder on
# purpose: it runs in one process with the stand-in, and steers it with
# events, as the backend tests do. So it uses the fixtures of conftest.py and
# the Python environment of the backend.
#
# The plain pytest step leaves it out (see addopts in backend/pyproject.toml).
# scripts/check.sh runs it as its last step, with "pytest -m browser".
import os
import re
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx2
import pytest
from conftest import SavedUser
from model_stand_in import ModelStandIn
from playwright.sync_api import Browser, Page, expect, sync_playwright
from playwright.sync_api import Error as PlaywrightError

pytestmark = pytest.mark.browser

BACKEND_FOLDER = Path(__file__).resolve().parent.parent
FRONTEND_FOLDER = BACKEND_FOLDER.parent / "frontend"
VITE_PROGRAM = FRONTEND_FOLDER / "node_modules" / ".bin" / "vite"

# How long a server may take to answer after it is started. The backend
# starts the runtime of the SDK, which takes a few seconds. Only reached when
# a server fails to start, so it does not slow a good run.
SERVER_START_SECONDS = 60.0
# How often the test asks whether a server answers yet.
SERVER_POLL_SECONDS = 0.1
# How long a server may take to stop before it is killed.
SERVER_STOP_SECONDS = 10.0
# How long Playwright waits for the page to show something. Only reached
# when the page does not show it, so it does not slow a good run.
PAGE_WAIT_MILLISECONDS = 15_000

# The answers of the stand-in. The pieces of each answer have no line break, so
# joined in order they give one paragraph of the page.
FIRST_MESSAGE = "Hello from Alice"
FIRST_ANSWER = ["Hello, ", "Alice."]
SECOND_MESSAGE = "Tell me more"
SECOND_ANSWER = ["First piece. ", "Second piece. ", "Third piece. ", "第四段。"]
# How many pieces of the second answer the stand-in sends before it holds.
PIECES_BEFORE_HOLD = 2


def free_port() -> int:
    # Asks the system for a port that is free now. Another program could
    # take it before the server does; then the server fails to start and the
    # test says so.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


def wait_until_answering(
    address: str, process: subprocess.Popen[bytes], log_file: Path
) -> None:
    deadline = time.monotonic() + SERVER_START_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(
                f"The server for {address} stopped at start, with code "
                f"{process.returncode}. It wrote:\n{log_file.read_text()}"
            )
        try:
            # trust_env=False: the call goes straight to 127.0.0.1, never
            # through a proxy of the machine.
            if httpx2.get(address, timeout=1.0, trust_env=False).status_code == 200:
                return
        except httpx2.TransportError:
            pass
        time.sleep(SERVER_POLL_SECONDS)
    pytest.fail(
        f"{address} did not answer within {SERVER_START_SECONDS} seconds. "
        f"The server wrote:\n{log_file.read_text()}"
    )


def start_server(
    command: list[str], folder: Path, environment: dict[str, str], log_file: Path
) -> subprocess.Popen[bytes]:
    # start_new_session puts the server and any process it starts in a
    # process group of their own, so stop_server can stop them all at once.
    with log_file.open("wb") as log:
        # The command is fixed in this file, never taken from input.
        return subprocess.Popen(  # noqa: S603
            command,
            cwd=folder,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def stop_server(process: subprocess.Popen[bytes], name: str, log_file: Path) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(SERVER_STOP_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    except ProcessLookupError:
        # The process group has ended already.
        process.wait()
    # pytest shows this only when the test fails.
    print(f"===== What the {name} wrote =====\n{log_file.read_text()}")


@pytest.fixture
def backend_address(model_key: str, tmp_path: Path) -> Iterator[str]:
    # The fixtures of conftest.py have set the environment of this process:
    # the database file, the folder of the session files, the address of the
    # stand-in, a model key made at run time, and no proxy. The backend gets
    # this environment, so the real key of the machine cannot reach it.
    port = free_port()
    log_file = tmp_path / "backend.log"
    process = start_server(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        BACKEND_FOLDER,
        dict(os.environ),
        log_file,
    )
    address = f"http://127.0.0.1:{port}"
    try:
        wait_until_answering(f"{address}/health", process, log_file)
        yield address
    finally:
        stop_server(process, "backend", log_file)


@pytest.fixture
def frontend_address(backend_address: str, tmp_path: Path) -> Iterator[str]:
    # Vite is started directly, not through "npm run dev", so the process
    # that the test stops is Vite itself.
    port = free_port()
    log_file = tmp_path / "frontend.log"
    process = start_server(
        [str(VITE_PROGRAM), "--host", "127.0.0.1", "--port", str(port), "--strictPort"],
        FRONTEND_FOLDER,
        {**os.environ, "POC_BACKEND_ADDRESS": backend_address},
        log_file,
    )
    address = f"http://127.0.0.1:{port}"
    try:
        # Through the proxy rule of the development server, so the whole
        # path to the backend answers before the browser starts.
        wait_until_answering(f"{address}/api/health", process, log_file)
        yield address
    finally:
        stop_server(process, "development server", log_file)


@pytest.fixture
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch()
        try:
            yield chromium
        finally:
            chromium.close()


@pytest.fixture
def page(browser: Browser, frontend_address: str) -> Iterator[Page]:
    # Asks for the servers, so they are stopped only after this fixture has
    # shown the page of a failed test.
    expect.set_options(timeout=PAGE_WAIT_MILLISECONDS)
    new_page = browser.new_page()
    new_page.set_default_timeout(PAGE_WAIT_MILLISECONDS)
    console: list[str] = []
    new_page.on(
        "console", lambda message: console.append(f"{message.type}: {message.text}")
    )
    try:
        new_page.goto(frontend_address)
        yield new_page
    finally:
        try:
            # pytest shows this only when the test fails.
            print(f"===== The page at the end: {new_page.url} =====")
            try:
                print(new_page.locator("body").inner_text())
            except PlaywrightError as error:
                # For example a page that has crashed. A new error here would
                # hide the failure of the test, so it is only printed.
                print(f"The text of the page could not be read: {error}")
            print("===== The console of the page =====")
            print("\n".join(console))
        finally:
            new_page.close()


def sign_in(page: Page, user: SavedUser) -> None:
    page.get_by_role("textbox", name="User name").fill(user.username)
    page.get_by_label("Password").fill(user.password)
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_text(f"Signed in as {user.username}")).to_be_visible()


def send(page: Page, text: str) -> None:
    page.get_by_role("textbox", name="Message", exact=True).fill(text)
    page.get_by_role("button", name="Send").click()


def test_two_users_chat_through_the_whole_product(
    page: Page,
    stand_in: ModelStandIn,
    model_key: str,
    add_user: Callable[[str], SavedUser],
) -> None:
    alice = add_user("alice")
    bob = add_user("bob")
    conversations = page.get_by_role("navigation", name="Conversations")
    your_messages = page.get_by_role("article", name="Your message", exact=True)
    answers = page.get_by_role("article", name="Answer", exact=True)
    stop_button = page.get_by_role("button", name="Stop")
    send_button = page.get_by_role("button", name="Send")

    # User A signs in and starts a conversation with the button of the page.
    sign_in(page, alice)
    page.get_by_role("button", name="New conversation").click()
    expect(page).to_have_url(re.compile(r"#/conversations/[^/]+$"))
    conversation_address = page.url
    expect(conversations.get_by_role("link", name="New conversation")).to_be_visible()
    expect(send_button).to_be_visible()

    # The first answer is held before its first piece: the page says that
    # the model is working.
    first_plan = stand_in.answer_and_hold(*FIRST_ANSWER, hold_after=0)
    send(page, FIRST_MESSAGE)
    expect(page.get_by_text("The model is working…")).to_be_visible()
    expect(stop_button).to_be_visible()
    first_plan.let_go()
    expect(answers).to_have_text(["".join(FIRST_ANSWER)])
    expect(send_button).to_be_visible()

    # The list shows the opening of the message as the title.
    expect(conversations.get_by_role("link", name=FIRST_MESSAGE)).to_be_visible()
    expect(conversations.get_by_role("link", name="New conversation")).to_have_count(0)

    # The second answer arrives in pieces. While the stand-in holds, the page
    # shows the pieces that were sent and none of the rest, and "Stop" shows
    # that the answer is still arriving.
    second_plan = stand_in.answer_and_hold(
        *SECOND_ANSWER, hold_after=PIECES_BEFORE_HOLD
    )
    send(page, SECOND_MESSAGE)
    expect(your_messages.last).to_have_text(SECOND_MESSAGE)
    growing_answer = answers.nth(1)
    expect(growing_answer).to_have_text("".join(SECOND_ANSWER[:PIECES_BEFORE_HOLD]))
    for piece in SECOND_ANSWER[PIECES_BEFORE_HOLD:]:
        expect(growing_answer).not_to_contain_text(piece.strip())
    expect(stop_button).to_be_visible()
    second_plan.let_go()
    expect(growing_answer).to_have_text("".join(SECOND_ANSWER))
    expect(send_button).to_be_visible()

    # After a reload the user is still signed in, the same conversation is
    # open, and the page shows the history.
    page.reload()
    expect(page.get_by_text("Signed in as alice")).to_be_visible()
    assert page.url == conversation_address
    expect(your_messages).to_have_text([FIRST_MESSAGE, SECOND_MESSAGE])
    expect(answers).to_have_text(["".join(FIRST_ANSWER), "".join(SECOND_ANSWER)])

    # User A signs out. User B signs in and does not see A's conversation.
    page.get_by_role("button", name="Sign out").click()
    sign_in(page, bob)
    # The list of B is an empty list element once it has been read.
    expect(conversations.get_by_role("list")).to_be_attached()
    expect(conversations.get_by_role("link")).to_have_count(0)
    expect(page.get_by_text(FIRST_MESSAGE)).to_have_count(0)

    # B opens the address of A's conversation.
    page.goto(conversation_address)
    expect(page.get_by_role("alert")).to_have_text("Conversation not found")
    expect(page.get_by_role("textbox", name="Message", exact=True)).to_have_count(0)

    # Every request that reached the stand-in carried the key of the test,
    # not a key of the machine.
    requests = stand_in.message_requests()
    assert len(requests) == 2
    assert all(request.headers["x-api-key"] == model_key for request in requests)
