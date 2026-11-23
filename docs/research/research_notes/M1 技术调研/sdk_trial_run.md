# Trial run of the Copilot SDK without a model key (2026-11-23)

The main agent ran this trial in the session's sandbox container. The owner agreed to it in conversation. Dates and times are US Eastern Time unless a log line says otherwise.

## Method

- Machine: Linux x86_64, glibc 2.39, Python 3.12 in a fresh virtual environment.
- Installed `microsoft-copilot-sdk==2.0.1` from PyPI. It pins runtime version 1.0.114.
- The trial process ran with a clean environment: no `GH_TOKEN`, no `GITHUB_TOKEN`, an empty home directory. So no GitHub sign-in was available to it.
- Outbound traffic went through a small logging proxy that recorded the host of each connection. `strace` also recorded every `connect` call, to catch connections that bypass the proxy.
- No real model was called. A local stand-in for a model provider answered on `127.0.0.1`. It speaks the OpenAI-style chat completions format with streaming and replies with a fixed sentence in ten pieces. It recorded what the runtime sent.
- All of this is evidence of the kind "measured data, one run on one machine". Nothing here tests a real provider.

## Results

1. Install and download.
   - The Python package is 13.6 MB of Python code, license MIT, with no runtime binary inside.
   - `python -m copilot download-runtime --in-process` took 9 seconds and contacted two hosts: `github.com` and `release-assets.githubusercontent.com`.
   - The download address is built in `copilot/_cli_version.py`: `https://github.com/github/copilot-cli/releases/download/v1.0.114/github-copilot-1.0.114-linux-x64.tgz`. So the runtime comes from the release packages of the Copilot CLI repository. `COPILOT_CLI_DOWNLOAD_BASE_URL` overrides the address, and `COPILOT_SKIP_CLI_DOWNLOAD` turns the download off.
   - Unpacked size: 196 MB. The runtime itself is `runtime.node`, a 165 MB stripped binary library. The bundle also holds `ripgrep`, `tgrep`, built-in skills and a browser plugin.
   - The bundle has license files only for two third-party parts (QuickJS, rquickjs). It has no license file for the runtime itself.
2. Start without GitHub sign-in.
   - The default connection is in-process (`InProcessRuntimeConnection`).
   - `client.start()` took 0.04 seconds. `get_status()` returned version 1.0.114, protocol 4, and `error_reporting=enabled`.
   - `get_auth_status()` returned `is_authenticated=False`, "Not authenticated". Sessions still worked with a BYOK provider. So the vendor's claim "no GitHub auth required" held in this run.
3. What `mode="empty"` demands. Two errors appeared before the run worked:
   - "CopilotClient(mode='empty') requires base_directory, session_fs, or a TcpRuntimeConnection. Empty mode needs explicit per-tenant storage and won't fall back to ~/.copilot."
   - Each session must pass `tools={"available_tools": [...]}`. An empty list is accepted and means no tools.
4. One chat turn with streaming.
   - `create_session` took 0.27 seconds. A turn took 1.56 seconds, of which 1.5 seconds were the stand-in's own delays.
   - The session received ten `assistant.message_delta` events, each with one piece in `delta_content`, then one `assistant.message` with the full text, then `session.idle`. About 45 other events arrived in the same turn (`assistant.streaming_delta`, `model.call_start`, `session.usage_info` and others, some of type "unknown").
5. Reading history back. `session.get_events()` returned 7 events, among them `user.message` and `assistant.message` with their `content`. So a user interface can read past messages through the SDK.
6. Persistence and resume.
   - Files appeared under `<base_directory>/session-state/<session id>/`: `events.jsonl`, `workspace.yaml`, `checkpoints/index.md`, `files/`, `research/`. There is also a lock file per session under `session-state/.session-operation-locks/`.
   - `workspace.yaml` stores the working directory of the process and a session name taken from the first prompt.
   - `list_sessions()` returned the session. After `resume_session`, the second request to the provider held the first turn's messages. So the history is replayed from disk.
7. What the runtime sends to the provider.
   - Every request carried a system prompt of about 7,100 characters, even in `mode="empty"` with no tools. It begins: "You are GitHub Copilot, an AI coding agent built by GitHub. You are an interactive tool that helps users with software engineering tasks." Its sections cover code changes, linting and testing, the `gh` command and similar topics.
   - The runtime also added a short note about the sandbox as a user message, and put `<current_datetime>` in front of the user's text.
   - The request used `Authorization: Bearer` with the configured key and a set of `x-stainless-*` headers.
8. Outside connections during the run. None. The logging proxy saw no host, and `strace` saw no connection other than the two to the local stand-in. This covers about five seconds of normal operation with no errors.
9. Memory of the Python process: 77 MB before start, 129 MB after `client.start()`, 163 MB with one session, 189 MB at the end of two turns.

## What this changes in the report

- "Does BYOK need a GitHub sign-in" moves from "vendor claim" to "held in one run against a local stand-in".
- "`get_events()` is unverified" is settled: it returns the stored events, with message content.
- "Where is the runtime downloaded from" is settled: GitHub release packages of `github/copilot-cli`.
- New: the default system prompt is that of a coding agent. A chat product must replace or adjust it. The SDK has a `system_message` option for this. That option was not tried.
- New: `mode="empty"` forces an explicit storage directory and an explicit tool list.

## Not tested

- A real model provider, and so real latency, token limits and the BYOK bugs listed in the basics note.
- The `system_message` option, tools, permission requests, compaction, two requests on one session at the same time.
- Whether the runtime contacts the vendor after errors or over a longer time. `error_reporting=enabled` suggests it may.
- The other connection types (child process, standalone server).

## The trial script

The script below is the whole trial. The stand-in provider and the logging proxy were two more throwaway scripts of about 80 and 50 lines. They are described under "Method" and are not kept.

```python
"""Trial run of the vendor's BYOK flow against a local stand-in provider.
Throwaway experiment. Not project code."""
import asyncio, json, os, sys, time
from copilot import CopilotClient, RuntimeConnection

STUB = "http://127.0.0.1:18081/v1"
SID = "trial-user1-conv1"

def rss_mb():
    for line in open("/proc/self/status"):
        if line.startswith("VmRSS"):
            return round(int(line.split()[1]) / 1024)

def reject_everything(request, invocation):
    # The stand-in model never asks for a tool. If the runtime asks anyway, refuse.
    raise RuntimeError("no tool is allowed in this trial")

def session_options():
    return dict(
        model="stub-model",
        permissions={"on_request": reject_everything},
        github={"capi": {"enabled": False}},
        inference={"default_provider": "byok", "providers": [{
            "name": "byok", "type": "openai", "base_url": STUB,
            "wire_api": "completions", "api_key": "dummy-key-for-the-local-stub"}]},
        events={"streaming": True},
        tools={"available_tools": []},
    )

async def one_turn(session, prompt):
    seen, deltas, done = [], [], asyncio.Event()
    final = {}
    def on_event(ev):
        t = ev.type.value if hasattr(ev.type, "value") else str(ev.type)
        seen.append(t)
        if t == "assistant.message_delta":
            deltas.append(getattr(ev.data, "delta_content", None))
        elif t == "assistant.message":
            final["content"] = getattr(ev.data, "content", None)
        elif t == "session.error":
            final["error"] = str(ev.data)[:500]
        elif t == "session.idle":
            done.set()
    off = session.on(on_event)
    t0 = time.time()
    await session.send(prompt)
    try:
        await asyncio.wait_for(done.wait(), timeout=60)
    except asyncio.TimeoutError:
        print("   TIMEOUT waiting for session.idle")
    off()
    print(f"   took {time.time()-t0:.2f}s; event types in order: {seen}")
    print(f"   delta pieces ({len(deltas)}): {deltas}")
    print(f"   final message: {final}")

async def main():
    print(f"[0] before start: RSS {rss_mb()} MB")
    conn = RuntimeConnection.for_default(base_directory=os.environ["TRIAL_BASE"])
    print(f"    default connection type: {type(conn).__name__}")
    client = CopilotClient(mode="empty", runtime=conn)
    t0 = time.time(); await client.start()
    print(f"[1] client.start() ok in {time.time()-t0:.2f}s; RSS {rss_mb()} MB")
    for name in ("get_status", "get_auth_status"):
        try:
            print(f"[2] {name}: {await getattr(client, name)()}")
        except Exception as e:
            print(f"[2] {name} failed: {type(e).__name__}: {str(e)[:300]}")

    t0 = time.time()
    session = await client.create_session(session_id=SID, **session_options())
    print(f"[3] create_session ok in {time.time()-t0:.2f}s; id={session.session_id}; RSS {rss_mb()} MB")
    print("[4] first turn"); await one_turn(session, "What is 2+2?")

    evs = await session.get_events()
    print(f"[5] get_events(): {len(evs)} events")
    for ev in evs:
        t = ev.type.value if hasattr(ev.type, "value") else str(ev.type)
        if t in ("user.message", "assistant.message"):
            print(f"     {t}: {getattr(ev.data, 'content', None)!r}")
    await session.disconnect()
    print("[6] disconnected")

    metas = await client.list_sessions()
    print(f"[7] list_sessions(): {[m.session_id for m in metas]}")

    session2 = await client.resume_session(SID, **session_options())
    print("[8] resumed; second turn"); await one_turn(session2, "And 3+3?")
    await session2.disconnect()
    await client.stop()
    print(f"[9] stopped; RSS {rss_mb()} MB")

asyncio.run(main())
```
