# Trial runs of the Copilot SDK (2026-11-23)

The main agent ran these trials in a session's sandbox container. The owner agreed to each in conversation. Dates and times are US Eastern Time unless a log line says otherwise.

There are three runs. The first two use a local stand-in for the model provider and no model key. The third calls a real model. It is under "Third run: a real model provider".

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
- New: the default system prompt is that of a coding agent. A chat product must replace it. The SDK's `system_message` option does this (see the second run below).
- New: `mode="empty"` forces an explicit storage directory and an explicit tool list.

## Second run: replacing the system prompt

Same setup, three sessions, one prompt each. The stand-in provider recorded the system message it received.

| `system_message` option | System message that reached the provider |
|---|---|
| not set | 7,123 characters, begins "You are GitHub Copilot, an AI coding agent built by GitHub" |
| `{"mode": "append", "content": <our text>}` | 7,198 characters: the same built-in prompt with our text added at the end |
| `{"mode": "replace", "content": <our text>}` | exactly our 75 characters and nothing else. The extra user message about the sandbox was also gone |

So with "replace" the application decides the whole system prompt. The basics note records the vendor's warning that "replace" also removes the SDK's own guardrails, so the application's prompt must carry any rules it needs.

## Third run: a real model provider

The owner asked for this run and supplied a Claude API key in the environment variable `POC_MODEL_API_KEY`. The trial process read the key from the variable. The key was never printed. After the run, a search of every file the run wrote found no copy of the key.

### The provider's data terms, checked before the run

The provider is Anthropic. An API key comes under its commercial terms. The main agent read all four pages on 2026-11-23 and checked each quoted sentence against the page text. They are vendor claims.

| Question | What the page says | Source |
|---|---|---|
| How long are requests kept? | "For Anthropic API users, we automatically delete inputs and outputs on our backend within 30 days of receipt or generation". Exceptions: a service with longer retention under the customer's control, such as the Files API; a separate agreement, such as zero data retention; enforcing the usage policy; the law. | [Privacy center: How long do you store my organization's data?](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data), dated 2026-07-01 |
| What if a request is flagged? | "We retain inputs and outputs for up to 2 years and trust and safety classification scores for up to 7 years if your chat is flagged by our automated trust and safety systems as violating our Usage Policy." | Same page |
| Are requests used for training? | "Anthropic may not train models on Customer Content from Services." The customer "retains all rights to its Inputs" and "owns its Outputs". | [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms), section B, effective 2025-06-17 |
| Where are requests processed? | The request setting `inference_geo` has two values. "global" is the default: "Inference may run in any available geography for optimal performance and availability." "us" means "Inference runs only in US-based infrastructure" and costs 1.1 times the standard price. Data at rest follows the workspace setting, and "us" is its only value. | [Data residency](https://platform.claude.com/docs/en/manage-claude/data-residency), undated |

Two more points from [API and data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention) (undated):

- Zero data retention is a separate arrangement that an organization requests from the vendor's sales team. A new personal account does not have it.
- That page says "Conversation content (your prompts and Claude's outputs) is not retained by default". The privacy center page says "within 30 days". The two pages do not say the same thing. For planning, assume up to 30 days.

So with the default settings a request may be processed outside the United States, and it may be kept for up to 30 days. Neither matters for this trial, which sent two test sentences. Both matter later, if real user text is sent.

### Method

- Same machine type as the first run. Python 3.12 in a fresh virtual environment, `microsoft-copilot-sdk==2.0.1`, runtime 1.0.114.
- The session ran on the owner's Default cloud environment. The key variable was set there.
- Step 1, a dry run with no real key. A new local stand-in answered on `127.0.0.1` in the Anthropic Messages format. The trial process had a dummy key and did not have the real key in its environment. The purpose was to see what the runtime sends before anything real was sent.
- Step 2, the real run. Provider type `anthropic`, address `https://api.anthropic.com`, model `claude-opus-5-5`, system prompt replaced with a short text of our own, no tools, streaming on. One turn, disconnect, resume, then a second turn that asks about the first.
- The model was the main agent's assumption for a trial. The owner has not chosen a model for the product.
- The trial process ran with a small environment: the program path, the key variable, an empty home directory, the proxy settings and the certificate file.
- Outbound traffic: a logging proxy stood in front of the container's own proxy and recorded the host of each connection. `strace` recorded every `connect` call. The container's settings send traffic for `api.anthropic.com` directly and not through the proxy, so that connection appears in `strace` as an address.
- Evidence of the kind "measured data, one run on one machine, one model".

### Results

1. It worked. Both turns returned a streamed answer from the real model. No error event arrived.
   - First turn. Prompt: "Please remember the word 'maple'. Then tell me what 2+2 is." Answer: `I'll keep "maple" in mind for this conversation, and 2+2 is 4.`
   - Second turn, after disconnect and resume. Prompt: "Which word did I ask you to remember?" Answer: `You asked me to remember "maple."` So resume replays the history to a real provider too.
2. What the runtime sends. This comes from the dry run. The first real request had the same body size as the first dry-run request, 622 bytes.
   - `POST /v1/messages`. The key goes in the `x-api-key` header.
   - Other headers: `anthropic-version: 2023-06-01`; `anthropic-beta: thinking-binding-controls-2026-08-01,mid-conversation-output-config-2026-07-01`; `user-agent: Anthropic/JS 0.94.0`; a set of `x-stainless-*` headers; `x-initiator: user`; `x-interaction-type: conversation-user`.
   - Body settings: `max_tokens: 48000`, `temperature: 1`, `thinking: {"type": "adaptive", "display": "summarized", "block_binding": {"prefix_mismatch_behavior": "drop_block"}}`, `output_config: {"effort": "medium"}`, `stream: true`.
   - System prompt: exactly our own text of 91 characters, with a prompt-cache marker. No built-in prompt.
   - User message: a `<current_datetime>` line, a blank line, then the user's text. The last user message carries a prompt-cache marker.
   - The runtime chose the thinking, effort, output limit and caching settings itself. The trial script set none of them. Whether the application can change them was not tested.
3. Events with a real model.
   - First turn: 16 `assistant.reasoning_delta`, one `assistant.reasoning`, 7 `assistant.message_delta`, one `assistant.message`, then `session.idle`. The reasoning events carry a summary of the model's thinking.
   - Second turn: no reasoning events, 3 `assistant.message_delta`, one `assistant.message`, then `session.idle`.
   - A chat interface must decide what to do with the reasoning events: show them, or ignore them.
4. Timing, as the runtime recorded it.
   - First turn: 3.0 seconds in total. The first piece arrived after 3.0 seconds. The reasoning pieces and the text pieces all arrived within about 12 milliseconds at the end. So the user would see nothing for 3 seconds and then the whole answer at once.
   - Second turn: 1.2 seconds in total. The first piece arrived after 0.6 seconds.
   - `client.start()` took 0.04 seconds and `create_session` took 0.23 seconds.
5. Tokens and cost.
   - First turn: 95 input tokens, 113 output tokens. 83 of the output tokens were reasoning.
   - Second turn: 257 input tokens, 13 output tokens. The request body grew from 622 to 2,237 bytes. The input grew because the history is sent again, and the history includes the reasoning block of the first turn. A replay of the stored conversation against the stand-in showed that block in the assistant message: 178 characters of reasoning text and a signature of 1,100 characters.
   - Total: 352 input and 126 output tokens. At $4 and $20 per million tokens for Claude Opus 5.5, that is about $0.004. Prices from the vendor's [pricing page](https://platform.claude.com/docs/en/about-claude/pricing), read 2026-11-23.
   - The runtime reports `cost: 0.0` for a BYOK provider. The application must work out cost from the token counts.
   - The cache counts were 0 in both turns. The likely reason is that the prompt is shorter than the provider's minimum for caching. This is an inference and was not checked.
   - The runtime's limits for this model: 128,000 prompt tokens and 48,000 output tokens.
6. What is stored on disk. `events.jsonl` held 15 events as plain text:
   - the user's text in two forms, as typed and with the date line added;
   - the system prompt;
   - the assistant's text;
   - the summary of the model's reasoning, and an opaque reasoning block that is sent back to the provider on the next turn;
   - usage records with token counts and timings;
   - the working directory of the process.
   - The key was in none of the files.
   - `get_events()` returned 6 events after the first turn, among them the user message and the assistant message.
7. Outside connections during the real run, about five seconds:
   - one TCP connection to `160.79.104.10` port 443, the address that `api.anthropic.com` resolved to at the time. Both requests used it;
   - one DNS socket to `8.8.8.8` port 53. The names asked for were not recorded;
   - four connections to the local name service socket `/var/run/nscd/socket`, which is not a network connection;
   - nothing through the logging proxy.
   - So this run made no connection to a host of the SDK's vendor. As before, this covers a short run with no errors.
8. `get_auth_status()` returned "Not authenticated", as in the first run. So a real provider also works with no GitHub sign-in.
9. Memory of the Python process: 77 MB before start, 130 MB after `client.start()`, 163 MB with one session, 185 MB at the end.

### What this changes

- "A real model provider" moves from "not tested" to "worked in one run, with Anthropic and one model".
- The Anthropic BYOK bugs listed in the basics note did not appear. All expected session events arrived (issue #1064). The output limit sent was 48,000 and not 8,192 (issue #955).
- New: the runtime turns on thinking, an effort level and prompt caching by itself.
- New: with a real model the first answer can arrive all at once after a wait, even with streaming on.
- New: the stored file keeps the summary of the model's reasoning next to the messages.
- New: the SDK does not work out cost under BYOK.

## Not tested

- Latency over many runs, long answers, token limits, and errors from the provider such as a wrong key or a rate limit. Other models and other providers. The open BYOK bugs listed in the basics note.
- Changing or turning off the thinking, effort, output limit and caching settings that the runtime chooses.
- Tools, permission requests, compaction, two requests on one session at the same time. The "customize" mode of `system_message`, which changes single sections of the built-in prompt.
- Whether the runtime contacts the vendor after errors or over a longer time. `error_reporting=enabled` suggests it may.
- The other connection types (child process, standalone server).

## The trial script of the first run

The script below is the whole first trial. The stand-in provider and the logging proxy were two more throwaway scripts of about 80 and 50 lines. They are described under "Method" and are not kept.

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

## The trial script of the third run

The script below is the whole third trial. It reads the provider address, the model name and the name of the key variable from the environment. The dry run and the real run used the same script with different values. The new stand-in for the Anthropic Messages format and the logging proxy were two more throwaway scripts of about 90 and 50 lines. They are described under "Method" of the third run and are not kept.

```python
"""Trial run of the vendor's BYOK flow against the Anthropic Messages API.
Throwaway experiment. Not project code.

Settings come from the environment, so no address, key or model name is fixed here:
  TRIAL_BASE      directory for the SDK's session files
  TRIAL_BASE_URL  address of the model provider
  TRIAL_MODEL     model name sent to the provider
  TRIAL_KEY_ENV   name of the variable that holds the key
"""
import asyncio, builtins, os, time
from collections import Counter
from copilot import CopilotClient, RuntimeConnection

KEY = os.environ[os.environ["TRIAL_KEY_ENV"]]
BASE_URL = os.environ["TRIAL_BASE_URL"]
MODEL = os.environ["TRIAL_MODEL"]
SID = "trial-user1-conv1"
SYSTEM_TEXT = ("You are a helpful assistant inside a chat product under test. "
               "Answer in one short sentence.")


def print(*args, **kwargs):
    # The key must never reach the output, even inside an error message.
    builtins.print(*[str(a).replace(KEY, "[key removed]") for a in args], **kwargs)


def rss_mb():
    for line in open("/proc/self/status"):
        if line.startswith("VmRSS"):
            return round(int(line.split()[1]) / 1024)


def reject_everything(request, invocation):
    # No tool is offered. If the runtime asks anyway, refuse.
    raise RuntimeError("no tool is allowed in this trial")


def session_options():
    return dict(
        model=MODEL,
        permissions={"on_request": reject_everything},
        github={"capi": {"enabled": False}},
        inference={"default_provider": "byok", "providers": [{
            "name": "byok", "type": "anthropic", "base_url": BASE_URL, "api_key": KEY}]},
        events={"streaming": True},
        tools={"available_tools": []},
        system_message={"mode": "replace", "content": SYSTEM_TEXT},
    )


def type_of(ev):
    return ev.type.value if hasattr(ev.type, "value") else str(ev.type)


async def one_turn(session, prompt):
    seen, deltas, done = [], [], asyncio.Event()
    final, marks, extra = {}, {}, []

    def on_event(ev):
        t = type_of(ev)
        seen.append(t)
        if t == "assistant.message_delta":
            marks.setdefault("first_delta", time.time())
            deltas.append(getattr(ev.data, "delta_content", None))
        elif t == "assistant.message":
            final["content"] = getattr(ev.data, "content", None)
        elif t == "session.error":
            final["error"] = str(ev.data)[:1500]
        elif t == "session.idle":
            done.set()
        if t in ("assistant.usage", "session.usage_info", "model.call_start",
                 "model.call_end", "model.call_failure", "session.warning"):
            extra.append(f"{t}: {str(ev.data)[:900]}")

    off = session.on(on_event)
    t0 = time.time()
    print(f"   prompt: {prompt!r}")
    await session.send(prompt)
    try:
        await asyncio.wait_for(done.wait(), timeout=120)
    except asyncio.TimeoutError:
        print("   TIMEOUT waiting for session.idle")
    off()
    total = time.time() - t0
    first = marks.get("first_delta")
    print(f"   took {total:.2f}s; first piece after "
          f"{(first - t0):.2f}s" if first else f"   took {total:.2f}s; no piece arrived")
    print(f"   event counts: {dict(Counter(seen))}")
    print(f"   delta pieces ({len(deltas)}): {deltas}")
    print(f"   final message: {final}")
    for line in extra:
        print(f"   {line}")


async def main():
    print(f"[0] provider {BASE_URL}, model {MODEL}; before start: RSS {rss_mb()} MB")
    conn = RuntimeConnection.for_default(base_directory=os.environ["TRIAL_BASE"])
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
    print(f"[3] create_session ok in {time.time()-t0:.2f}s; RSS {rss_mb()} MB")
    print("[4] first turn")
    await one_turn(session, "Please remember the word 'maple'. Then tell me what 2+2 is.")

    evs = await session.get_events()
    print(f"[5] get_events(): {len(evs)} events")
    for ev in evs:
        t = type_of(ev)
        if t in ("user.message", "assistant.message"):
            print(f"     {t}: {getattr(ev.data, 'content', None)!r}")
    await session.disconnect()
    print("[6] disconnected")

    metas = await client.list_sessions()
    print(f"[7] list_sessions(): {[m.session_id for m in metas]}")

    # The key is passed again on resume. Leaving it out was not tested.
    session2 = await client.resume_session(SID, **session_options())
    print("[8] resumed; second turn")
    await one_turn(session2, "Which word did I ask you to remember?")
    await session2.disconnect()
    await client.stop()
    print(f"[9] stopped; RSS {rss_mb()} MB")


asyncio.run(main())
```
