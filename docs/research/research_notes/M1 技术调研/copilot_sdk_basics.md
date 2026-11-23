# GitHub Copilot SDK basics (state as of 2026-11-23)

## Method note
- Access date for all sources: 2026-11-23 (US Eastern Time).
- About 25 pages were fetched or searched. All fetches went through WebFetch, which returns a model-written summary of the page, not the raw page. So READ means "fetched, summary read". Code samples may be condensed by that summary and must be checked against the source before use.
- Labels: READ = page fetched. SNIPPET = seen only in a search result. INFERENCE = my own reasoning. "unverified" = from memory with no source (none used).
- Evidence kinds: VENDOR = vendor claim. MEASURED = measured data. ONE PERSON = one person's experience.
- Direct GitHub API and raw.githubusercontent.com fetches failed (HTTP 403 / 404). No GitHub CLI tool was available to me. So I could not list every release or read every doc file.
- Naming warning: the product was "GitHub Copilot SDK". In Oct-Nov 2026 it is being renamed "Microsoft Copilot SDK". Sources use both names. I use "the SDK".

## A. What it is

### Takeaway
The SDK is a library that embeds the Copilot agent runtime (the engine behind Copilot CLI) in your own app. The brief's picture is partly outdated: since v2 (Nov 2026) the runtime is by default loaded inside your own process, not run as a separate CLI process. It reached general availability on 2026-06-02, and it is now being renamed and moved to the Microsoft organization.

### Findings
- Description: "Embed Copilot's agentic workflows in your application"; same engine as Copilot CLI. READ, VENDOR, page live Nov 2026. [microsoft/copilot-sdk README](https://github.com/microsoft/copilot-sdk)
- Architecture, v2: all SDKs speak JSON-RPC (protocol 4) to the runtime. By default a native Rust runtime is loaded into your process through a C ABI (in-process, no Node.js, no separate process). Alternatives: a spawned child process (stdio or TCP), or a standalone runtime server (`copilot-runtime --server`) that many clients attach to over TCP. In-process hosting gives "no crash isolation or sandboxing". READ, VENDOR. [README](https://github.com/microsoft/copilot-sdk); [v2 breaking changes](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)
- Architecture, v1 / preview: each SDK talked to a Copilot CLI server over JSON-RPC and required the CLI. SNIPPET, VENDOR (secondary summary of the Jan 2026 announcement). [Changelog 2026-01-14](https://github.blog/changelog/2026-01-14-copilot-sdk-in-technical-preview/)
- Languages: Node.js/TypeScript, Python, Go, .NET, Rust, Java (Rust and Java new at GA). Clojure and C++ SDKs are community-made and "not supported by GitHub". READ, VENDOR. [GA changelog 2026-06-02](https://github.blog/changelog/2026-06-02-copilot-sdk-is-now-generally-available/); [README](https://github.com/microsoft/copilot-sdk)
- License: MIT. READ, VENDOR. [README](https://github.com/microsoft/copilot-sdk); [PyPI](https://pypi.org/project/microsoft-copilot-sdk/)
- Timeline: technical preview 2026-01-14 ([changelog](https://github.blog/changelog/2026-01-14-copilot-sdk-in-technical-preview/), SNIPPET); public preview 2026-04-02 ([changelog](https://github.blog/changelog/2026-04-02-copilot-sdk-in-public-preview/), SNIPPET, title only); GA 2026-06-02 ("API surface is now stable and production-ready after coordinated cleanup based on preview feedback") (READ, VENDOR); rename notice 2026-10-28 ("No immediate changes are required for existing users"; phased move to the Microsoft org, no dates) ([changelog](https://github.blog/changelog/2026-10-28-github-copilot-sdk-is-becoming-microsoft-copilot-sdk), READ, VENDOR); SDK 2.0 announced at Ignite, article dated 2026-11-17 ([AlphaSignal](https://alphasignal.ai/news/microsoft-s-copilot-sdk-2-0-runs-95x-faster-by-ditching-containers-for-rust), READ, secondary).
- Current version: v2.0.1 "Latest" released 2026-11-18; pre-releases v2.0.2-preview.0 to .7 from 2026-11-19 to 2026-11-23. READ, VENDOR (release list, no year shown on page, year inferred from context). [Releases](https://github.com/microsoft/copilot-sdk/releases)
- Release rhythm: in the CHANGELOG fetch, v0.1.30 (2026-03-03), v0.2.0 (03-20), v0.2.2 (04-10), v1.0.2 (06-18), v1.0.7 (07-16), v1.0.13 (09-04), v1.0.14 (09-16). Then v2.0.x in Nov with daily pre-releases. READ, VENDOR. [CHANGELOG](https://github.com/microsoft/copilot-sdk/blob/main/CHANGELOG.md). Note: this CHANGELOG view had no v2 entries, so it looked stale or cached. INFERENCE: the file was behind the releases page when I read it.
- Breaking changes: v0.2.0 (2026-03-20) had many Python breaks (keyword-only args, required permission handler, removed config classes, private modules). v2.0 (Nov 2026) has more: package rename, required `mode`, flat options moved into groups, `provider` replaced by `inference`, in-process by default. Protocol 4 is required, and SDK and runtime must be upgraded together. READ, VENDOR. [CHANGELOG](https://github.com/microsoft/copilot-sdk/blob/main/CHANGELOG.md); [v2 breaking changes](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)
- Compatibility break for Microsoft Agent Framework: its .NET and Python adapters "are not compatible with v2". READ, VENDOR. [v2 breaking changes](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)
- INFERENCE: three majors-worth of API change in about 8 months (0.x to 1.0 to 2.0) means any PoC code needs a pinned version.

## B. Setup with your own model API key

### Takeaway
With BYOK you need no Copilot subscription, according to the vendor's auth table. The table does not say whether a GitHub account is needed (see the main agent's check at the end). But the Copilot runtime still runs. It is bundled and downloaded by the SDK, so no separate CLI install is needed. Billing and rate limits then come from your model provider.

### Findings
- Install: no separate Copilot CLI install by default. Node.js, .NET, Python and Rust packages handle the runtime. Go and Java need extra steps. READ, VENDOR. [README](https://github.com/microsoft/copilot-sdk)
- Python: runtime is downloaded on first use, or ahead with `python -m copilot download-runtime --in-process`. Cache on Linux: `~/.cache/copilot-sdk/...`. `COPILOT_CLI_PATH` selects a binary. `COPILOT_SKIP_CLI_DOWNLOAD=1` stops the download. READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)
- INFERENCE: first start needs internet access to fetch the runtime (or a pre-baked image). Restricted networks would need the offline path.
- Auth options: signed-in GitHub user, GitHub OAuth app, environment tokens (`COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`), server-to-server tokens, BYOK. Classic `ghp_` tokens are not supported. READ, VENDOR. [Auth methods](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate); [README](https://github.com/microsoft/copilot-sdk)
- Subscription needed? Table: BYOK = "No" ("No GitHub Copilot subscription required", "Direct billing with your model provider"). Other methods need a Copilot subscription. READ, VENDOR. [Auth methods](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate)
- BYOK providers: OpenAI and compatible endpoints; Microsoft Foundry / Azure OpenAI (`openai` or `azure` type); Anthropic; Google (Gemini, "experimental"); Ollama; Foundry Local; vLLM, LiteLLM and other OpenAI-compatible servers. READ, VENDOR. [BYOK doc in repo](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md); [GitHub Docs BYOK](https://docs.github.com/en/copilot/how-tos/copilot-sdk/authenticate-copilot-sdk/bring-your-own-key)
- BYOK config: `inference.providers` entries with `name`, `type`, `baseUrl`; models under `inference.models`; credentials via `apiKey`, `apiKeyCommand`, `bearerToken` or `bearerTokenProvider`; `wireApi` = `completions` (default) or `responses`; a `model` is required or you get "Model not specified". To switch off Copilot-hosted inference set `github.capi.enabled: false`. READ, VENDOR. [BYOK doc](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md)
- BYOK is key-based only. Entra ID, managed identities, third-party identity providers are not supported (README); but a repo doc `azure-managed-identity.md` and a bearer-token callback exist, flagged experimental in a .NET post. So the exact limit is unclear. READ, VENDOR. [README](https://github.com/microsoft/copilot-sdk); [setup folder](https://github.com/microsoft/copilot-sdk/tree/main/docs/setup); [.NET dev blog, 2026-10-19](https://devblogs.microsoft.com/dotnet/bring-your-own-model-to-the-github-copilot-sdk-with-csharp/)
- BYOK still runs the Copilot runtime: "BYOK changes where the model request goes"; it is not "the Copilot SDK without Copilot". READ, one vendor engineer's blog. [.NET dev blog](https://devblogs.microsoft.com/dotnet/bring-your-own-model-to-the-github-copilot-sdk-with-csharp/)
- Missing under BYOK: only models your provider has; rate limits and usage tracking come from your provider; not counted against Copilot premium requests. READ, VENDOR. [BYOK doc](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md)
- Also missing without GitHub auth: /delegate (cloud agent), the GitHub MCP server, GitHub code search. SNIPPET only (search summary of CLI docs, not opened). [Search result](https://docs.github.com/en/copilot/how-tos/copilot-sdk/auth/authenticate)
- Billing without BYOK: "same model as the Copilot CLI", each prompt counts toward the usage allowance. Available to Copilot Free users too. READ, VENDOR. [README FAQ](https://github.com/microsoft/copilot-sdk); [GA changelog](https://github.blog/changelog/2026-06-02-copilot-sdk-is-now-generally-available/)
- Status label for BYOK: one search summary called BYOK "public preview"; the BYOK docs page itself has no status label. SNIPPET vs READ conflict, not resolved.

## C. The Python API

### Takeaway
The Python SDK is async-first, needs Python 3.11+, and has a small session API: create client, create session, `send` or `send_and_wait`, listen to events. PyPI lists it as "Development Status 3 - Alpha" even though the vendor says GA. The package name changed between v1 and v2.

### Findings
- Package: v2 is `pip install microsoft-copilot-sdk`; v1 and the GA changelog used `pip install github-copilot-sdk`. Import stays `import copilot`. Uninstall the old package first. READ, VENDOR. [v2 breaking changes](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md); [GA changelog](https://github.blog/changelog/2026-06-02-copilot-sdk-is-now-generally-available/)
- PyPI: microsoft-copilot-sdk 2.0.1 (2026-11-18), pre-releases 2.0.2rc2 to rc7 (2026-11-20 to 11-23), `>=3.11`, MIT, classifier "3 - Alpha", Python 3.11 to 3.14. READ, measured metadata. [PyPI](https://pypi.org/project/microsoft-copilot-sdk/)
- Async: yes, async/await native; `async with` supported; manual `start()`/`stop()` also works. READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)
- Minimal example (repo license MIT). From the BYOK doc. The main agent fetched the raw file again on 2026-11-23 and replaced the condensed copy with the text below. Official source: [docs/auth/byok.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md). READ, VENDOR:

```python
import asyncio
import os
from copilot import CopilotClient
from copilot.session import PermissionHandler

FOUNDRY_MODEL_URL = "https://<resource-name>.openai.azure.com/openai/v1/"
# Set FOUNDRY_API_KEY environment variable


async def main():
    client = CopilotClient(mode="coding-agent")
    await client.start()

    session = await client.create_session(
        model="gpt-5.2-codex",
        permissions={"on_request": PermissionHandler.approve_all},
        github={"capi": {"enabled": False}},
        inference={
            "default_provider": "byok",
            "providers": [
                {
                    "name": "byok",
                    "type": "openai",
                    "base_url": FOUNDRY_MODEL_URL,
                    "wire_api": "responses",  # Use "completions" for older models
                    "api_key": os.environ["FOUNDRY_API_KEY"],
                }
            ],
        },
    )

    done = asyncio.Event()

    def on_event(event):
        if event.type.value == "assistant.message":
            print(event.data.content)
        elif event.type.value == "session.idle":
            done.set()

    session.on(on_event)
    await session.send("What is 2+2?")
    await done.wait()

    await session.disconnect()
    await client.stop()


asyncio.run(main())
```
- The non-BYOK quickstart is described (not quoted): `CopilotClient(mode="coding-agent")`, `create_session(model=..., permissions=...)`, `send_and_wait(prompt)`, print the assistant message. `send_and_wait` can return `None` if no assistant message came. READ, VENDOR. [Getting started](https://github.com/microsoft/copilot-sdk/blob/main/docs/getting-started.md); [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)
- Mode: `mode` is required in v2. `coding-agent` (was `copilot-cli`) enables CLI-like tools. `empty` turns off ambient tools and is advised for multi-user servers. READ, VENDOR. [v2 breaking changes](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)
- System prompt: `system_message` with mode `append`, `replace` or `customize` (section-level). `replace` removes the SDK guardrails. READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)
- Model: `model=` at session creation; `reasoning_effort` where supported; `list_models()`. READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)
- Tools: `@define_tool` decorator with Pydantic parameter models; low-level `Tool` class; options `skip_permission`, `defer`, `overrides_built_in_tool`. Also MCP servers and hooks (pre/post tool use, permission requests). READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md); [GA changelog](https://github.blog/changelog/2026-06-02-copilot-sdk-is-now-generally-available/)
- Permissions: in v2, omitting a permission handler leaves requests pending (neither approved nor denied). A handler that raises means "reject". READ, VENDOR. [v2 breaking changes](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md); [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)
- Errors: `JsonRpcError` with `code` and `data`; `session.abort`/`delete` failures raise JSON-RPC errors; default RPC timeout 30 s (overridable per call); `force_stop()` fails pending calls. READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md); [CHANGELOG](https://github.com/microsoft/copilot-sdk/blob/main/CHANGELOG.md)
- Maturity vs other SDKs: the vendor ships all six from one repo with one protocol. The Python-only break list is long (v0.2.0). Commands and UI elicitation were Node-only until v0.2.1 (2026-04-03). In-process transport is "experimental" for Node, Rust, Python, Go as of v1.0.7, and became the default in v2. PyPI says Alpha. READ, VENDOR. [CHANGELOG](https://github.com/microsoft/copilot-sdk/blob/main/CHANGELOG.md); [PyPI](https://pypi.org/project/microsoft-copilot-sdk/)
- INFERENCE: I found no independent comparison of Python vs TypeScript quality. Parity looks close but Python is not the lead SDK (Node is the original).

## D. Streaming output

### Takeaway
Turn on streaming with `events={"streaming": True}` on the session. Then you get many `assistant.message_delta` events, each with `delta_content`, and one final `assistant.message` with the full text. `session.idle` marks the end of the turn.

### Findings
- Event names: `assistant.message_delta` (incremental `delta_content`), `assistant.message` (complete text, always sent), `session.idle`. READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md); [Getting started](https://github.com/microsoft/copilot-sdk/blob/main/docs/getting-started.md)
- Python usage: `session.on(handler)`; match on `event.type` or `event.data` classes (`AssistantMessageData`, `SessionIdleData`). Print each delta as it arrives, finish on `session.idle`. READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)
- Sub-agent events carry `agent_id` and do not complete a `send_and_wait`. READ, VENDOR. [Python README](https://github.com/microsoft/copilot-sdk/blob/main/python/README.md)
- v2 event change: `tool.execution_partial_result` replaced by `tool.shell_output`. v2.0.2-preview.4: `assistant.message` no longer includes `encryptedContent`. READ, VENDOR. [v2 breaking changes](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md); [Releases](https://github.com/microsoft/copilot-sdk/releases)
- Known problems, BYOK streaming: #1090 "Streaming reasoning and intent when using BYOK" (closed 2026-05-20); #1229 vLLM BYOK reasoning not surfaced (closed 2026-09-08); #1064 Anthropic BYOK missing session events (closed 2026-05-16); #1402 sub-agents never emit `assistant.reasoning` close event (open, 2026-05-23). READ (issue titles and dates only, bodies not read), one-person reports. [Issue search](https://github.com/microsoft/copilot-sdk/issues?q=is%3Aissue+python+byok)
- #2546 "When hit max_output_tokens, some events are not emitted" (closed as duplicate 2026-10-26). READ (title). Same search link.
- INFERENCE: the event stream is Copilot-specific, not the raw provider stream. The backend must translate it for the browser (Researcher 3's topic).

## E. Limits and preview status

### Takeaway
The vendor calls it generally available and semver-versioned. But there is no documented rate limit from the SDK itself (limits come from the provider under BYOK). I found no clear statement about telemetry defaults. Platform notes for Linux are thin and mostly in issues.

### Findings
- Production claim: "generally available and follows semantic versioning". READ, VENDOR. [README FAQ](https://github.com/microsoft/copilot-sdk)
- Preview-period warning: "may not yet be suitable for production use" (Jan 2026). SNIPPET, VENDOR, now historical. [Changelog 2026-01-14](https://github.blog/changelog/2026-01-14-copilot-sdk-in-technical-preview/)
- Rate limits: under BYOK, "your provider's limits, not Copilot's". No SDK-level limits found. READ, VENDOR. [BYOK doc](https://github.com/microsoft/copilot-sdk/blob/main/docs/auth/byok.md)
- Platforms: Python cache paths exist for Linux, macOS, Windows. Linux x64 prebuilds exist. Issue #2897 (open, 2026-11-04): Linux x64 prebuild `1.0.29-preview.1` links shared OpenSSL and aborts under a VS Code snap (glibc mismatch). It affects the VS Code snap, not plain servers. READ, one-person reports. [Issue 2897](https://github.com/microsoft/copilot-sdk/issues/2897)
- Issue #1630 "models.list -32603 in Kubernetes" (closed 2026-10-26). READ (title only). [Issue search](https://github.com/microsoft/copilot-sdk/issues?q=is%3Aissue+python+byok)
- Telemetry: OpenTelemetry tracing with W3C trace context is supported (user-side telemetry). Whether the runtime sends usage data to GitHub/Microsoft by default: not found. READ, VENDOR. [GA changelog](https://github.blog/changelog/2026-06-02-copilot-sdk-is-now-generally-available/); [Observability docs index](https://github.com/microsoft/copilot-sdk/blob/main/docs/observability/README.md)
- Terms: repo license is MIT. GitHub's generic pre-release terms forbid production use and allow telemetry, but I could not confirm they apply now that the SDK is GA. SNIPPET. [Pre-release terms](https://docs.github.com/en/site-policy/github-terms/github-pre-release-license-terms)
- Multi-user guidance from the vendor: use `mode="empty"`, one session ID per user and request, per-user token, allowlist tools (`available_tools`), set a permission handler, set an idle timeout, check session ownership in your backend, do not share one GitHub token across users. READ, VENDOR. [multi-tenancy.md](https://github.com/microsoft/copilot-sdk/blob/main/docs/setup/multi-tenancy.md)
- Vendor caveat: no built-in session locking (concurrent access to one session is undefined); BYOK keys must be supplied again on resume; hosting is "mostly self-managed". READ, secondary report of vendor statements. [AlphaSignal, 2026-11-17](https://alphasignal.ai/news/microsoft-s-copilot-sdk-2-0-runs-95x-faster-by-ditching-containers-for-rust)
- Vendor performance claim: one-turn overhead 5.25 s (v1) vs 55.3 ms (v2), memory 1,383 MB vs 126 MB for 10 clients. Microsoft's own warmed benchmark, no hardware given. READ, VENDOR claim, treat as unverified. [AlphaSignal](https://alphasignal.ai/news/microsoft-s-copilot-sdk-2-0-runs-95x-faster-by-ditching-containers-for-rust)

## F. Criticism and failure reports

### Takeaway
I found real bug reports, mostly BYOK-related, and version-pairing trouble. I found no independent production post-mortem of the SDK. General dislike of Copilot is not about the SDK and I do not count it.

### Findings
- #2826 (closed 2026-10-14): a Python SDK 1.0.18 user with a local OpenAI-compatible BYOK server saw `send_and_wait` time out after 60 s waiting for `session.idle` after the runtime moved from 1.0.92 to 1.0.94. Cause not confirmed; the user went back to a paired older version. READ, one person's experience. [Issue 2826](https://github.com/microsoft/copilot-sdk/issues/2826)
- #2905 (open, 2026-11-05): Python/OpenTelemetry, runtime 1.0.105 omits trace context on BYOK Responses requests. READ (title). [Issue list](https://github.com/microsoft/copilot-sdk/issues)
- #2926 (open, 2026-11-17): Python, a redelivered `external_tool.requested` runs a non-idempotent tool handler twice. READ (title). [Issue list](https://github.com/microsoft/copilot-sdk/issues)
- #2748 (open, 2026-09-22): BYOK `maxOutputTokens` never reaches the upstream request. #2756 (open): `maxContextWindowTokens` ignored. #955 (closed 2026-04-06): Anthropic BYOK `max_tokens` hard-coded at 8192 caused silent truncation. #1072 (closed): compaction does not trigger for BYOK Anthropic. #1073 (closed): cache token counts never filled. READ (titles, dates). [Issue search](https://github.com/microsoft/copilot-sdk/issues?q=is%3Aissue+python+byok)
- #2915 (open, 2026-11-11): `<current_datetime>` and random `prompt_cache_key` block cross-session prompt caching. INFERENCE: this may raise token cost for many users. READ (title). Same search link.
- #2928 (open, 2026-11-18): every live session spawns all extensions and a full MCP set. INFERENCE: higher per-session cost for many concurrent chats. READ (title). [Issue list](https://github.com/microsoft/copilot-sdk/issues)
- Open issue count: 178 on 2026-11-23. READ, measured. [Issue list](https://github.com/microsoft/copilot-sdk/issues)
- Docs mismatch: the docs mix names (`@github/...`, `microsoft-copilot-sdk`) and one fetched CHANGELOG lagged the releases page. v2.0.1 itself "restores legacy imports", which suggests the v2 rename broke some users. READ, VENDOR. [Releases](https://github.com/microsoft/copilot-sdk/releases)
- Sentiment piece on the Jan 2026 preview: mostly general "AI fatigue" about GitHub marketing, not SDK engineering. SNIPPET, one outlet. [devactivity](https://devactivity.com/insights/github-copilot-sdk-preview-developer-community-reacts-to-ai-push/)
- Where I looked: repo issues (titles), search for blogs and forums. Not found: independent blog posts reporting a production deployment, Hacker News or Reddit threads about the SDK itself.

## G. Alternatives (names only, as mentioned in my sources)
- Microsoft Agent Framework (Python and .NET adapters for the SDK exist, v1 only). [v2 breaking changes](https://github.com/microsoft/copilot-sdk/blob/main/docs/v2-breaking-changes.md)
- Community Copilot SDK ports for Clojure and C++ (not alternatives, same runtime). [README](https://github.com/microsoft/copilot-sdk)
- A "CopilotKit" article appeared in search; it is a different project (frontend agent toolkit). SNIPPET. [ranjankumar.in](https://ranjankumar.in/copilotkit-in-production-where-the-abstraction-holds-and-where-you-are-on-your-own)
- No other agent SDKs were named in the sources I read.

## Fitness for the first PoC (all INFERENCE)
- No hard blocker found for "own model API key, Python backend, no Copilot subscription". The auth table, BYOK doc and a Python BYOK example all say it is supported. "No GitHub account" is not stated by any source read and stays unverified until someone runs the example without one.
- Risk, fast change: v2.0.1 is 5 days old, daily pre-releases, PyPI says Alpha, package renamed. Pin exact versions of SDK and runtime together.
- Risk, BYOK quality: several BYOK bugs (token limits, events, Anthropic) and one timeout report after a runtime upgrade. Test the exact provider and model early.
- Risk, runtime still Copilot: BYOK still downloads and runs the Copilot runtime. Needs network at first start or a pre-baked image.
- Risk, security: `coding-agent` mode can expose the server's files; use `mode="empty"`, a permission handler, tool allowlist. Do not copy `approve_all` from the examples.
- Risk, cost and scale: per-session extension and MCP spawn (#2928), weak prompt caching (#2915), no session locking.
- Risk, terms: unclear whether any GitHub pre-release or Copilot terms still apply to BYOK use; owner should read the repo SUPPORT.md and license pages before a company use.
- Fit question: the SDK is built for coding-agent behavior (files, shell). A chat-only PoC uses a small part of it. A plain model client would be simpler; deciding that is for the owner.

## Could not find or verify
- Full release list (v2.0.0 date, v1.x tags): API and raw-file fetches failed (403/404); I used the releases page and a possibly stale CHANGELOG.
- The BYOK "Limitations" section verbatim, the Authentication Overview page in the repo (404), and the full list of features lost without GitHub auth (only a search snippet).
- Whether BYOK is "public preview" or GA (conflicting).
- Telemetry sent by the runtime by default, and how to disable it (`opentelemetry.md` and TelemetryConfig not read).
- Terms of use specific to the SDK, and whether GitHub pre-release terms apply now. SUPPORT.md not read.
- Rate limits or quotas on the SDK or runtime itself; Linux container requirements (glibc, OpenSSL, base image); Docker-specific reports.
- Verbatim Python quickstart (fetch tool summarized it); the BYOK example above is condensed by the tool.
- Issue bodies: only titles and dates for most issues; only #2826 and #2897 were read in detail.
- Independent production experience reports or benchmarks (the 95x figure is vendor-only).
- Whether the PyPI "Alpha" classifier is intentional or simply not updated.

## Main agent's check (2026-11-23)
The main agent fetched five of this note's sources again. Raw files on `raw.githubusercontent.com` could be fetched this time.
- PyPI `microsoft-copilot-sdk`: 2.0.1 released 2026-11-18, pre-releases up to 2.0.2rc7 (2026-11-23), "3 - Alpha", Python >= 3.11, MIT, `from copilot import CopilotClient`. Matches.
- GA changelog of 2026-06-02: "The GitHub Copilot SDK is now generally available", six languages, BYOK listed. Matches.
- GitHub Docs auth page: the table says BYOK needs no Copilot subscription and bills through the model provider. Matches. Correction: the page does not say whether a GitHub account is needed, and the BYOK doc only says "GitHub identity remains independent". The note first said "no GitHub account"; that wording was removed in sections B and "Fitness".
- `docs/auth/byok.md`: the Python example was copied again in full (section C). Provider type values on the page are `openai`, `azure`, `anthropic`, `google`.
- `python/README.md`: `pip install microsoft-copilot-sdk`, Python 3.11+, streaming switched on with `events={"streaming": True}`, `assistant.message_delta` with `delta_content`, modes `coding-agent` and `empty`, history through `get_events()` with no further detail. Matches.
