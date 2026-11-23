# GitHub Copilot SDK for several users

Researcher 2 of 3, technical research for the first PoC. Access date for all sources: 2026-11-23 (US Eastern Time).

## Method note

- I fetched about 14 pages and ran 5 searches. Fetched pages were read through a summarizing tool, not word for word. Treat quotes as close, not exact.
- Labels: READ = I fetched the page. SNIPPET = seen only in a search result. INFERENCE = my own reasoning.
- Evidence kinds: vendor claim (docs by the SDK authors), measured data (numbers someone measured), one person's experience (an issue or post).
- Raw `main` docs have no page date. I write "date unknown (main branch, fetched 2026-11-23)". Dated items come from the changelog, PyPI and issues.
- The repository now lives at `github.com/microsoft/copilot-sdk` (the old `github/copilot-sdk` links redirect). The project is moving from the name "GitHub Copilot SDK" to "Microsoft Copilot SDK". The PyPI package `github-copilot-sdk` is marked deprecated in favor of `microsoft-copilot-sdk`. [READ, https://github.com/microsoft/copilot-sdk, https://pypi.org/project/github-copilot-sdk/, vendor claim, date unknown]
- Version facts: PyPI `github-copilot-sdk` 1.0.35, released 2026-11-18, classifier "Alpha", Python >= 3.11. [READ, PyPI, vendor data]. Changelog shows SDK "v2" with the runtime hosted in-process by default. [READ, https://raw.githubusercontent.com/microsoft/copilot-sdk/main/CHANGELOG.md, vendor claim]
- Big change versus older posts: the SDK no longer needs the Copilot CLI. It uses a separate "runtime" (`copilot-runtime`). Older material (2026 H1) talks about a CLI server and `cli_url`. The current docs do not mention `cli_url`. [READ, backend-services.md, vendor claim]

## A. The session model

Takeaway: A session is one conversation held by the runtime. The application can choose the session id. State lives as plain files on the disk of the machine that runs the runtime. The SDK does not store state in a remote service (except "cloud sessions", an optional separate feature).

- Who chooses the id: you may pass your own `session_id` (Python option on `create_session`). If you do not, the runtime makes one and you must store it yourself. Docs recommend ids like `user-{userId}-{taskId}`. [READ, https://raw.githubusercontent.com/microsoft/copilot-sdk/main/docs/features/session-persistence.md, vendor claim, date unknown]
- Python README confirms `session_id (str): Custom session ID`. [READ, https://raw.githubusercontent.com/microsoft/copilot-sdk/main/python/README.md, vendor claim, date unknown]
- Where state lives: `~/.copilot/session-state/{sessionId}/`. You can move it with `COPILOT_HOME` or `--config-dir` (server), or `baseDirectory` (SDK-owned runtime). [READ, session-persistence.md, multi-tenancy.md, same dates unknown, vendor claim]
- Files in that folder, per the docs: `events.jsonl` (event log = conversation history), `workspace.yaml` (metadata), `checkpoints/` (compaction summaries as Markdown), `plan.md`, `files/` (artifacts). Tool call results are kept too. [READ, session-persistence.md, vendor claim]
- Not stored: provider/API keys ("never persisted to disk") and in-memory tool state. [READ, session-persistence.md, vendor claim]
- Working directory and config (model, system message, tools, MCP servers, BYOK provider, `workingDirectory`) are options you pass on create and can change on resume. [READ, session-persistence.md, vendor claim]
- Optional: a `sessionFs` provider can route session files to storage you control instead of the local disk (options `sessionStatePath`, `initialCwd`). [READ, multi-tenancy.md, vendor claim]
- The docs say a session is resumable once it has handled a message. [READ, session-persistence.md, vendor claim]
- Format in SQL terms (INFERENCE): each session is a folder, and `events.jsonl` is like an append-only log table with one row per event. There is no database to query.

## B. Persistence and resume

Takeaway: Resume, list and delete exist in the Python client. History lives in `events.jsonl` on disk, so it survives restarts if the folder survives. The docs do not say that your app must keep its own copy of messages. They also document no simple "get messages" call for a UI.

API names (Python):
- Create: `client.create_session(model=..., session_id=..., permissions={"on_request": ...})`. [READ, session-persistence.md]
- Resume: `await client.resume_session(session_id, *, permissions=..., ...)` returns `CopilotSession`. Raises `RuntimeError` if the session does not exist. [READ, https://raw.githubusercontent.com/microsoft/copilot-sdk/main/python/copilot/client.py (read in part; 349k characters, I read up to char 300000), vendor source code, date unknown]
- List: `await client.list_sessions(filter: SessionListFilter | None = None) -> list[SessionMetadata]`. Filter by working directory, git root, repository, branch. `SessionMetadata` has `session_id`, `start_time`, `modified_time`, `is_remote`, `summary`, `context`, `client_name`, `last_client_name`. [READ, client.py, same]
- Metadata for one: `await client.get_session_metadata(session_id)` returns `None` if missing. `get_last_session_id()` also exists. [READ, client.py]
- Delete: `await client.delete_session(session_id)`. "Permanently delete ... all its data from disk". [READ, client.py]. Added to Python by PR #153, merged 2026-01-23. [SNIPPET, search result about PR #153, one-line summary only]
- Leave without deleting: `session.disconnect()` frees memory and keeps disk data. Python context manager `async with await client.create_session(...)` does the same. [READ, session-persistence.md]
- The session-persistence page only shows `listSessions` and `deleteSession` in TypeScript. Python names above come from the source file. [READ, vendor claim]
- Past messages for a UI: the Python README lists `get_events()` for "Session history". I did not verify its signature or return shape. No `get_messages` was found. The session-management page says there is no peer-history read endpoint, and that history can be read from `events.jsonl` via `sessionStatePath`. [READ, python/README.md and docs/session-management.md, vendor claim] Which way is better for a chat UI is unverified.

What survives (vendor claims, READ, session-persistence.md):
- Runtime restart, backend restart, container migration: history, tool results, `plan.md`, `files/` survive, "provided the storage is still available". You must re-supply BYOK provider config (including the key) and the permission handler on every resume.
- Machine or container loss: state is lost unless the folder is on a persistent volume. Docs say to mount `~/.copilot/session-state/`. [READ, scaling.md]
- In-memory tool state is lost. Approve-once permission answers are not restored. Session-scoped approvals are restored only if marked as a human answer. [READ, session-persistence.md]
- Damaged transcript: `allowTranscriptRecovery` (default true) may repair it. With false, a lossy load fails with JSON-RPC error -32075. Optional log rotation with `COPILOT_SESSION_EVENT_LOG_ROTATION_BYTES` makes `events.N.jsonl`; resume reads only the head file. [READ, session-persistence.md]

Long conversations:
- "Infinite sessions" with background compaction. Python: `state={"infinite_sessions": {"enabled": True, "background_compaction_threshold": 0.80, "buffer_exhaustion_threshold": 0.95}}`. Thresholds are context-fill ratios. Summaries go to `checkpoints/`. [READ, python/README.md and session-persistence.md, vendor claim]
- Compaction shortens what the model sees. The full event log stays on disk (INFERENCE from file layout; not stated outright).
- Idle timeout: off by default for runtimes you attach to. Set `--session-idle-timeout <seconds>` on the server. Idle sessions are evicted from memory, not deleted from disk (INFERENCE from the logs in issue #2889 "Evicting idle session" followed by resumes). [READ]

Own copy of history? The docs say state persists automatically and a disconnect is safe. They say you must store the session id and ownership yourself. They do not say whether to mirror messages into your database. (INFERENCE: a small table of session id, owner, title, timestamps is needed regardless; mirroring messages is optional.)

## C. Isolation between users

Takeaway: The SDK does NOT enforce separation between users. It has no user or tenant concept. The vendor says plainly that the application owns routing and authorization. The SDK gives per-session state, per-session credentials and explicit tool lists. You must check ownership before every resume or delete.

- "The app owns request routing and authorization. The SDK and runtime provide per-session state, per-session auth, and explicit tool registration." [READ, https://raw.githubusercontent.com/microsoft/copilot-sdk/main/docs/setup/multi-tenancy.md, vendor claim, date unknown]
- "Your app must enforce which user can access which session." [READ, scaling.md, vendor claim]
- Rules for a shared runtime: unique ids that include a tenant or user boundary; store ownership in your database; check ownership before `resumeSession`, `deleteSession` or any UI action naming a session; allowlist tools. Pitfall list includes "trusting client-supplied session IDs without ownership checks". [READ, multi-tenancy.md, vendor claim]
- The docs' own sample checks access by parsing the user id out of the session id prefix. The review text calls this fragile. [READ, scaling.md, vendor claim] (INFERENCE: use a database lookup instead.)
- Mode: use `mode: "empty"` on shared servers. `"coding-agent"` can expose host file tools. Python constructor shows `CopilotClient(mode="coding-agent", runtime=...)`. [READ, multi-tenancy.md and python/README.md]
- File system: the host filesystem is shared by everyone on the same runtime if host tools are on. Session state is under `COPILOT_HOME/session-state/{id}` unless routed via `sessionFs`. [READ, multi-tenancy.md]
- Remembered permission grants (`permissions.json`, `settings.json`, `config.json`) are not partitioned by session id. Sessions in the same provider namespace share them. Isolate by giving each tenant its own namespace. [READ, multi-tenancy.md, vendor claim]
- Write block on approval files is "defense in depth, not a tamper-proof storage boundary". [READ, multi-tenancy.md]
- Permission requests without a human: you pass a handler. `PermissionHandler.approve_all` is built in. A custom handler is `def on_permission_request(request, invocation) -> PermissionRequestResult`. [READ, python/README.md] (INFERENCE: for a headless backend, write a handler that allows only an explicit list of tools and denies the rest, and never use approve_all with host tools.) Docs warn that a permission-provider error is not consent. [READ, multi-tenancy.md]
- Credentials: BYOK key is passed per session (`inference.providers`, with `github.capi.enabled: false`). Per-user GitHub token goes in `github.token` on create or resume. Docs advise against sharing one `github.token` across users. Attached clients cannot set client-level `github.token`. [READ, backend-services.md and multi-tenancy.md, vendor claim]
- Under BYOK the shared project key is the same for all sessions (INFERENCE). `bearerTokenProvider` receives `sessionId` for per-session scoping since v1.0.5, 2026-07-01. [READ, CHANGELOG.md, vendor claim]
- Open question from a user: whether account-level "Copilot Memory" can leak into a "fresh" session under first-party inference. Issue #2772, opened 2026-09-24, open, no maintainer reply seen. The reporter calls it a docs question, not observed leakage. [READ, https://github.com/microsoft/copilot-sdk/issues/2772, one person's experience] Whether it applies under BYOK is unverified.
- No built-in session locking. Two requests to the same session need your own lock or queue. [READ, session-persistence.md and scaling.md, vendor claim]

## D. Deployment shapes

Takeaway: Three shapes are documented: runtime inside your process (default), runtime as a child process, or a standalone runtime server over TCP that many clients share. The vendor lists "runtime per user" as strongest isolation and "shared runtime" as cheapest. No one has published memory or start-up numbers for the idle runtime that I could find.

1. In-process (v2 default). Native Rust library loaded into your Python process. "Not a sandbox", no crash isolation; a native crash can kill the app. All clients in the process share env and working directory. Bundle must match OS, CPU, and Linux C library. Doc gives no memory or start-up figures and no container guidance. Python pre-download: `python -m copilot download-runtime --in-process`. [READ, https://raw.githubusercontent.com/microsoft/copilot-sdk/main/docs/setup/in-process-runtime.md, vendor claim]
2. Spawned child process: `RuntimeConnection.for_spawned_stdio()` or `for_spawned_tcp()`. SDK owns it; gives crash isolation. Env `COPILOT_SDK_DEFAULT_CONNECTION=stdio` switches the default. [READ, in-process-runtime.md and python/README.md]
3. Standalone server: `copilot-runtime --server --port 4321`. Python client: `RuntimeConnection.for_tcp("localhost", 4321, connection_token=...)`. One server serves many clients and concurrent sessions. Plain TCP, no TLS. Loopback binds need no token; non-loopback binds refuse to start without `COPILOT_CONNECTION_TOKEN`. No official Docker image: build your own from release tarballs. [READ, https://raw.githubusercontent.com/microsoft/copilot-sdk/main/docs/setup/backend-services.md, vendor claim]
4. Runtime per user (strongest isolation, highest cost) and runtime per session are not separately documented; per user is in scaling.md, per session is not mentioned (could not verify). [READ, scaling.md]

Other points:
- Concurrency limit: no hard limit documented. The sample `SessionManager` caps active sessions at 50 and evicts one on overflow. The doc itself says the eviction is not true LRU and does not check in-flight requests. [READ, scaling.md, vendor sample]
- Process dies: sessions on disk survive; in-memory work is lost. A server is a single point of failure. A failed cancel blocks a session until `recoverSession`. [READ, backend-services.md]
- More than one backend instance: allowed if session state is on shared storage (NFS or cloud files) or users are pinned by sticky sessions. No built-in locking or load balancing. File-based state needs a shared filesystem. [READ, scaling.md, vendor claim]
- Kubernetes sample: Deployment with 3 replicas, one PersistentVolumeClaim at the session-state path, Service on port 4321. Azure Container Instances with an Azure File share. [READ, scaling.md, vendor claim]
- Production checklist from the vendor: TTL cleanup, health checks (`client.getStatus()`), persistent storage, secret manager, monitoring, locking, graceful drain. [READ, scaling.md, backend-services.md]
- Idle timeout guidance: 15 to 30 minutes for chat backends. [READ, multi-tenancy.md, vendor claim]
- Multi-client detail: v1.0.13 (2026-09-04) cleanup uses `session.detach` so one client disconnecting does not end a session others use. [READ, CHANGELOG.md, vendor claim]
- Memory cost measured by one user (see F): resuming a large session costs about 3x its `events.jsonl` size in runtime memory. [READ, issue #2889, one person's measurement]

## E. Examples

- `github/copilot-sdk-server-sample`: MIT. Express + React chat, several app servers behind a load balancer, session files pushed to an `rsync-filestore` container after each turn, local copy deleted when all sockets close. Per-session virtual file system and virtual bash; only non-file tools enabled. Its README says it has no authentication or session authorization, minimal limits, limited isolation, and "multi-user deployment patterns are still evolving". Not Python. Last commit date not shown (15 commits). [READ, https://github.com/github/copilot-sdk-server-sample, vendor sample, date unknown]
- Official docs samples (TypeScript Express, Redis lock, Kubernetes YAML) in `docs/setup/`. License of repo: MIT. [READ, https://github.com/microsoft/copilot-sdk, vendor]
- Java cookbook "multiple sessions" and "persisting sessions" pages exist. [SNIPPET, search result, github.github.io/copilot-sdk-java, not opened]
- A FastAPI multi-user example: none found. [SNIPPET: a search returned none]
- Community SDK forks exist (Clojure, C++). Not relevant; not checked. [READ, repo README summary]

## F. Criticism and failure reports

Takeaway: I found open issues about memory growth after resuming large sessions, permission recovery, and docs gaps on isolation. I found no report of one user reading another's session, and no report of data corruption. Coverage is thin, because I read only the first results page of issue search (page 1 of 8).

- Issue #2889, opened 2026-11-01, open. Runtime memory grows when large sessions are resumed and disconnected. Measured by the reporter: about 3x `events.jsonl` size per resume (250 MB -> +750 MB; 439 MB -> +1.37 GB); about +46 MB per cycle with no recovery for a 250 MB session; two runtimes at 12.8 GB and 8.0 GB. Small (15 MB) sessions stayed flat. Version: SDK 1.0.27-unstable, runtime 1.0.100-1, macOS. One other user reported about 12 GB on Windows. [READ, https://github.com/microsoft/copilot-sdk/issues/2889, measured data from one person's setup]
- Issue #540, opened 2026-02-23, closed 2026-03-04 as no-repro. `resumeSession()` returned a session that did not answer; reporter's web chat disabled resume. Maintainer could not reproduce and added tests (PR #665). Old SDK 0.1.25. [READ, https://github.com/microsoft/copilot-sdk/issues/540, one person's experience]
- Issue #2852 (open, 2026-10-16): pending permission recovery, handler not re-invoked after resume. [SNIPPET from issue list, not opened]
- Issue #2871 (open, 2026-10-26): tool calls keep failing after a session abort until another chat turn. [SNIPPET]
- Issue #2791 (closed, 2026-09-29): Rust router could send requests to a replaced session registration. This is the closest to an isolation bug; it is Rust-only and fixed. [SNIPPET]
- Issue #2749 (closed, 2026-09-28): `session.create` deadlocks when a `SessionFsProvider` is bound. [SNIPPET]
- Issue #2821 (open, 2026-10-08): .NET Windows in-process access violation. #2793 (closed 2026-10-26): Rust in-process use-after-free risk. [SNIPPET] These support the docs' warning that in-process has no crash isolation.
- Issue #2750 (closed): `send_and_wait` resolved on a sub-agent's idle/error event. [SNIPPET]
- Doc gaps stated by the vendor: no built-in locking; sample eviction ignores in-flight requests; Redis lock release not atomic; sticky-session hash reshuffles. [READ, scaling.md, vendor admission]
- Status wording: PyPI classifier "Alpha"; docs said "technical preview" in older snippets. [READ PyPI; SNIPPET for older wording]
- Independent blog posts about multi-user problems: a search found none. [SNIPPET, one search]

## What this means for a small multi-user PoC

All items here are INFERENCE. I do not choose.

1. Shared runtime, in-process (default). One Python process, many sessions, session id per conversation, an ownership table in your database. Cost: no crash isolation, no sandbox, shared working directory; one native crash ends every user's chat. Simplest to start. Needs `mode="empty"`, an allow-list permission handler, your own per-session lock.
2. Shared standalone runtime server (TCP) next to the backend. Same logic, but the runtime can restart separately and several backend instances can attach. Cost: extra process to run and secure (token, network), one single point of failure, no official image, session folder must sit on persistent storage.
3. One runtime per user. Vendor's strongest isolation. Cost: more processes and memory (no measurements found), a process manager, idle shutdown logic. Likely more than a first PoC needs.
4. Ephemeral sessions plus your own history. Create a session per request, disconnect in `finally`, and replay messages from your database. Cost: you build and store the history yourself and lose the SDK's compaction and tool state. Avoids resume bugs and disk folders. The vendor documents "ephemeral" as a pattern for stateless APIs. [READ, scaling.md]
5. Whatever shape: keep a small database table (session id, owner user id, title, created, last used). Check it before every resume, send and delete. The SDK will not do this. Set an idle timeout. Re-send the BYOK key on each resume. Avoid very large sessions until #2889 is fixed.

## Could not find or verify

- Exact date of the docs pages on `main` (no page dates). Docs.github.com versions exist but I only saw them in search results. [SNIPPET]
- The signature and return shape of `get_events()` in Python and whether it suits a chat history UI. I read client.py only up to char 300000 of about 349000.
- Whether `delete_session` and `list_sessions` on a shared TCP runtime enforce anything per user (almost certainly not; unverified). `list_sessions` returns all sessions "known to the server", so it must be filtered by your own ownership table (INFERENCE from the signature).
- Memory and start-up cost of an idle runtime, and measured concurrency limits. Not found.
- Runtime-per-session as a documented pattern. Not found.
- Whether session files can be encrypted or whether `sessionFs` has a ready database-backed provider. Not found.
- Behavior of Copilot Memory under BYOK (issue #2772 unanswered).
- Only page 1 of 8 of the issue search was read; most issue bodies other than #2889, #2772, #540 were seen only as titles.
- Whether sample repo `copilot-sdk-server-sample` has recent commits; license MIT as shown on its page.
- Independent third-party reports (blogs, forums) on multi-user use: none found in two searches.
- Anything from my own memory was not used. No claim here is unverified-from-memory.

## Main agent's check (2026-11-23)
The main agent fetched five of this note's sources again. The facts match, with one caveat.
- Repository page `github.com/microsoft/copilot-sdk`: README title "Microsoft Copilot SDK", the sentence "GitHub Copilot SDK is becoming Microsoft Copilot SDK", MIT, a runtime "separate from the Copilot CLI", and "generally available and follows semantic versioning". Caveat: the page showed no redirect notice and its Issues link still pointed to `github/copilot-sdk`. So the move is in progress, and which address redirects to which is not verified.
- PyPI `github-copilot-sdk`: 1.0.35 released 2026-11-18, "3 - Alpha", Python >= 3.11, marked deprecated in favor of `microsoft-copilot-sdk`. Matches.
- `docs/setup/multi-tenancy.md`: "the application owns request routing and authorization", `mode: "empty"` required for shared use, session state under `COPILOT_HOME/session-state/{sessionId}` unless routed through `sessionFs`, no user or tenant concept. Matches.
- `docs/features/session-persistence.md`: the `~/.copilot/session-state/{sessionId}/` path, the file list, "API keys are never persisted to disk", the Python create and resume examples, and "The SDK doesn't provide built-in session locking". Matches.
- Issue 2889: opened 2026-11-01, the memory numbers, the versions and macOS. Matches. The fetched page showed a "Backlog" status and did not clearly show open or closed.
