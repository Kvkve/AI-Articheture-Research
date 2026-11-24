# A small local server that stands in for the model provider in the tests.
# It speaks the streaming format of the Anthropic Messages API, because
# "anthropic" is the provider type the product uses, so the tests take the
# same path through the SDK's runtime as a real run.
#
# The server runs in its own thread. Each request takes the next plan from a
# queue, so a test says beforehand how the next answers behave. Plans signal
# with threading.Event objects, so a test waits for "the request arrived" or
# "the connection was closed" and never for a fixed time.
import json
import select
import socket
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

# How often a held answer looks whether the runtime has closed the
# connection. Short, so a test that waits for the close does not wait long.
CLOSE_CHECK_SECONDS = 0.05

# A held answer gives up after this long, so a test that forgets to let it go
# cannot keep a server thread alive for ever.
LONGEST_HOLD_SECONDS = 30.0


@dataclass
class RecordedRequest:
    method: str
    path: str
    headers: dict[str, str]
    body: dict[str, Any]

    def all_text(self) -> str:
        # The whole body as one text, for tests that look for a word anywhere
        # in what the runtime sent.
        return json.dumps(self.body)

    def system_prompt(self) -> str:
        system = self.body.get("system", "")
        if isinstance(system, str):
            return system
        return "".join(part.get("text", "") for part in system)

    def message_texts(self) -> list[tuple[str, str]]:
        # Each message as (role, text), with the text parts joined.
        texts = []
        for message in self.body.get("messages", []):
            content = message["content"]
            if isinstance(content, str):
                text = content
            else:
                text = "".join(
                    part.get("text", "") for part in content if part["type"] == "text"
                )
            texts.append((message["role"], text))
        return texts


@dataclass
class Plan:
    # The pieces of text to send, in order.
    pieces: list[str] = field(default_factory=list)
    # When set, send this many pieces, then wait until the test calls
    # let_go(), then send the rest.
    hold_after: int | None = None
    # When set, answer with this status and an error body instead.
    error_status: int | None = None
    # When True, the error body repeats the key that the request carried, as
    # a careless provider might.
    echo_key: bool = False
    # When True, accept the request and send nothing at all.
    silent: bool = False

    arrived: threading.Event = field(default_factory=threading.Event)
    finished: threading.Event = field(default_factory=threading.Event)
    connection_closed_early: threading.Event = field(default_factory=threading.Event)
    _go_on: threading.Event = field(default_factory=threading.Event)
    pieces_sent: int = 0

    def let_go(self) -> None:
        self._go_on.set()


class ModelStandIn:
    def __init__(self) -> None:
        self.requests: list[RecordedRequest] = []
        self._plans: list[Plan] = []
        self._all_plans: list[Plan] = []
        self._lock = threading.Lock()
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler_class())
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def address(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host!s}:{port}"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        # Let every held answer go, so no server thread stays blocked.
        for plan in self._all_plans:
            plan.let_go()
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()

    def answer(self, *pieces: str) -> Plan:
        return self._add(Plan(pieces=list(pieces)))

    def answer_and_hold(self, *pieces: str, hold_after: int) -> Plan:
        return self._add(Plan(pieces=list(pieces), hold_after=hold_after))

    def fail(self, status: int, echo_key: bool = False) -> Plan:
        return self._add(Plan(error_status=status, echo_key=echo_key))

    def stay_silent(self) -> Plan:
        return self._add(Plan(silent=True))

    def message_requests(self) -> list[RecordedRequest]:
        with self._lock:
            return [r for r in self.requests if r.path.endswith("/messages")]

    def _add(self, plan: Plan) -> Plan:
        with self._lock:
            self._plans.append(plan)
            self._all_plans.append(plan)
        return plan

    def _next_plan(self) -> Plan:
        with self._lock:
            if self._plans:
                return self._plans.pop(0)
        # A request that no test planned for still gets a short answer.
        plan = Plan(pieces=["(no plan)"])
        self._all_plans.append(plan)
        return plan

    def _record(self, request: RecordedRequest) -> None:
        with self._lock:
            self.requests.append(request)

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        stand_in = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                # Keep the test output quiet.
                return

            def do_GET(self) -> None:
                stand_in._record(
                    RecordedRequest("GET", self.path, dict(self.headers), {})
                )
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
                stand_in._record(
                    RecordedRequest("POST", self.path, dict(self.headers), body)
                )
                if not self.path.endswith("/messages"):
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                plan = stand_in._next_plan()
                plan.arrived.set()
                try:
                    self._follow(plan)
                finally:
                    plan.finished.set()

            def _follow(self, plan: Plan) -> None:
                if plan.silent:
                    self._wait_for_go_on(plan)
                    return
                if plan.error_status is not None:
                    self._send_error(plan)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Connection", "close")
                self.end_headers()
                try:
                    self._send_event(
                        "message_start",
                        {
                            "type": "message_start",
                            "message": {
                                "id": "msg_stand_in",
                                "type": "message",
                                "role": "assistant",
                                "model": stand_in_model_name(stand_in),
                                "content": [],
                                "stop_reason": None,
                                "stop_sequence": None,
                                "usage": {"input_tokens": 10, "output_tokens": 1},
                            },
                        },
                    )
                    self._send_event(
                        "content_block_start",
                        {
                            "type": "content_block_start",
                            "index": 0,
                            "content_block": {"type": "text", "text": ""},
                        },
                    )
                    for number, piece in enumerate(plan.pieces):
                        if number == plan.hold_after and not self._wait_for_go_on(plan):
                            return
                        self._send_event(
                            "content_block_delta",
                            {
                                "type": "content_block_delta",
                                "index": 0,
                                "delta": {"type": "text_delta", "text": piece},
                            },
                        )
                        plan.pieces_sent += 1
                    self._send_event(
                        "content_block_stop", {"type": "content_block_stop", "index": 0}
                    )
                    self._send_event(
                        "message_delta",
                        {
                            "type": "message_delta",
                            "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                            "usage": {"output_tokens": len(plan.pieces)},
                        },
                    )
                    self._send_event("message_stop", {"type": "message_stop"})
                except (BrokenPipeError, ConnectionResetError):
                    plan.connection_closed_early.set()

            def _send_event(self, name: str, data: dict[str, Any]) -> None:
                text = f"event: {name}\ndata: {json.dumps(data)}\n\n"
                self.wfile.write(text.encode())
                self.wfile.flush()

            def _send_error(self, plan: Plan) -> None:
                status = plan.error_status or 500
                message = f"The stand-in answers {status} on purpose."
                if plan.echo_key:
                    message += f" The key was {self.headers.get('x-api-key')}."
                body = json.dumps(
                    {
                        "type": "error",
                        "error": {"type": "api_error", "message": message},
                    }
                ).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)

            def _wait_for_go_on(self, plan: Plan) -> bool:
                # Returns False when the runtime closed the connection first.
                waited = 0.0
                while not plan._go_on.wait(CLOSE_CHECK_SECONDS):
                    waited += CLOSE_CHECK_SECONDS
                    if self._client_has_closed() or waited > LONGEST_HOLD_SECONDS:
                        plan.connection_closed_early.set()
                        return False
                return True

            def _client_has_closed(self) -> bool:
                connection: socket.socket = self.connection
                readable, _, _ = select.select([connection], [], [], 0)
                if not readable:
                    return False
                try:
                    return connection.recv(1, socket.MSG_PEEK) == b""
                except OSError:
                    return True

        return Handler


def stand_in_model_name(stand_in: ModelStandIn) -> str:
    # The answer names the model that the last request asked for.
    requests = stand_in.message_requests()
    if not requests:
        return "stand-in"
    return str(requests[-1].body.get("model", "stand-in"))


@contextmanager
def running_stand_in() -> Iterator[ModelStandIn]:
    stand_in = ModelStandIn()
    stand_in.start()
    try:
        yield stand_in
    finally:
        stand_in.stop()
