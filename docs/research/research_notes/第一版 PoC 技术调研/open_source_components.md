# Open-source components a small PoC could borrow (research note)

Access date for every source: 2026-11-23 (US Eastern Time). Researcher 3 of 3.

## Method note

- I made about 55 tool calls: about 35 page fetches that worked, about 12 web searches, and a few fetches that failed (listed at the end).
- GitHub's API was blocked (HTTP 403). So I used repository pages, raw LICENSE files and the `releases.atom` feeds. The feeds give exact release dates.
- Labels: READ = I fetched the page. SNIPPET = seen only in a search result. INFERENCE = my own reasoning. "Unverified" = from memory, no source.
- Fetched pages were summarized by a small model, so "READ" means the fetched text, not that I saw every character.
- Evidence kinds: VENDOR = claim by the project or company about itself. MEASURED = data such as dates, star counts, license text. EXPERIENCE = one person's write-up or forum post.
- Repository pages do not show commit dates in the fetched text. Where I have no date, I say "date unknown". Star counts are rough and come from the page text on the access date.
- License names come from the raw LICENSE file where I could read it. Otherwise they come from the README or page (marked).

## A. Scaffolding for React and FastAPI

Takeaway: The official FastAPI full-stack template is MIT and active, but it is large (auth, PostgreSQL, Docker, Traefik, e-mail, end-to-end tests). A learner should read it, not copy it whole. For a small PoC, `create-vite` (frontend only) plus a hand-written FastAPI app is the smaller path. FastAPI itself has a built-in way to stream now.

### A1. fastapi/full-stack-fastapi-template
- License MIT, copyright Sebastián Ramírez. [READ, MEASURED] [LICENSE](https://raw.githubusercontent.com/fastapi/fastapi/master/LICENSE) is for FastAPI; the template's file: [LICENSE](https://raw.githubusercontent.com/fastapi/full-stack-fastapi-template/master/LICENSE), date unknown.
- About 46.3k stars. Latest commits 2026-11-16 ("Update release notes", a dependency bump). [READ, MEASURED] [repo](https://github.com/fastapi/full-stack-fastapi-template), [commit feed](https://github.com/fastapi/full-stack-fastapi-template/commits/master.atom) (2026-11-16).
- Includes: FastAPI with SQLModel and Pydantic; React with TypeScript, Vite, Tailwind, shadcn/ui, TanStack Query and Router; PostgreSQL; JWT sign-in and password recovery by e-mail; pytest and Playwright tests; Docker Compose with Traefik and automatic HTTPS; GitHub Actions CI; Mailpit and React Email. [READ, VENDOR (README text)] [repo](https://github.com/fastapi/full-stack-fastapi-template), page date unknown.
- The repo page shows no GitHub "Releases". It has 1,551 commits. [READ, MEASURED]
- Backing: the FastAPI organization (author is the FastAPI creator). [READ] The copyright line names a person, not a company.
- Learner load (INFERENCE): high. Two languages, an ORM, token sign-in, containers, a reverse proxy and e-mail. Each is a topic of its own.
- How to cut it down (INFERENCE): keep `backend/app` models, one router, the sign-in dependency and the test setup. Drop e-mail, Traefik, Playwright and the generated client at first. Keep SQLite or the Postgres container only.
- The template has no chat feature or streaming endpoint in the README text I read. [READ] (I did not open the source tree.)

### A2. Vite `create-vite` (react-ts template)
- `npm create vite@latest my-app -- --template react-ts` makes a React and TypeScript project. Vite needs Node.js 20.19+ or 22.12+. Docs show Vite 8 (v8.3.7). [READ, VENDOR] [Vite guide](https://vite.dev/guide/), page date unknown.
- License MIT, "VoidZero Inc. and Vite contributors". [READ, MEASURED] [LICENSE](https://raw.githubusercontent.com/vitejs/vite/main/LICENSE)
- Backing: VoidZero Inc. (company). Release date and star count: not collected.
- Learner load (INFERENCE): low. A few config files. The owner can treat the build tool as a black box.

### A3. FastAPI alone (backend base)
- FastAPI is MIT (copyright 2018, Sebastián Ramírez). [READ, MEASURED] [LICENSE](https://raw.githubusercontent.com/fastapi/fastapi/master/LICENSE)
- Latest releases: 0.165.0 on 2026-11-18, 0.164.0 on 2026-11-18, 0.163.2 on 2026-11-17. [READ, MEASURED] [releases feed](https://github.com/fastapi/fastapi/releases.atom)
- It is version 0.x, with several releases a week (INFERENCE from the feed). Expect small breaking changes; pin the version.

### A4. Reference only: vercel-labs/ai-sdk-preview-python-streaming
- A FastAPI backend with a Next.js frontend that streams with `useChat` over the Vercel data stream protocol. 364 stars, 31 commits. [READ, MEASURED] [repo](https://github.com/vercel-labs/ai-sdk-preview-python-streaming), page date unknown.
- License: the raw LICENSE file returned 404. License not verified.
- A search result said its `/api/chat` endpoint returns `text/event-stream` and takes a `protocol` query parameter. [SNIPPET, VENDOR] [AI SDK Python Streaming Preview](https://docsearch.algolia.com/mcp/docs/repo/vercel-labs/ai-sdk-preview-python-streaming), date unknown.
- Next.js is not needed by the PoC (INFERENCE), so use it to read how Python emits the protocol, not as a base.

## B. Chat components for React

Takeaway: Only two kinds fit a small PoC. One is a plain, UI-only kit (chatscope) where you write the streaming yourself. The other is a library with a runtime (assistant-ui, or Vercel's `useChat`), which saves work but ties you to a wire format. Big chat apps (Open WebUI, LibreChat, Chainlit, LobeHub) are references, not parts.

### B1. assistant-ui
- What: React library with thread, message list, composer, markdown and streaming display. Adapters for AI SDK, LangGraph, AG-UI, A2A, Google ADK, and a "data stream" runtime. Optional paid "Assistant Cloud" for thread storage. [READ, VENDOR] [repo](https://github.com/assistant-ui/assistant-ui), page date unknown.
- Backend link: `useDataStreamRuntime({ api: "/api/chat" })` sends a POST with `messages`, `tools`, `system`, `threadId`. It accepts two formats: `ui-message-stream` (SSE from AI SDK v5+) and the older `data-stream` (detected by header `x-vercel-ai-data-stream: v1`). [READ, VENDOR] [data stream docs](https://www.assistant-ui.com/docs/runtimes/custom/data-stream), date unknown.
- Python path: package `assistant-stream` on PyPI, with `DataStreamResponse`. State updates travel as lines like `aui-state:[...]`. The page says the default will move to SSE later. [READ, VENDOR] [assistant transport docs](https://www.assistant-ui.com/docs/runtimes/custom/assistant-transport), date unknown. The `assistant-stream` license was not stated there: license not verified.
- Lock-in (INFERENCE): medium. You must emit one of its formats, or write a custom adapter. Its Python helper is its own format. A "local runtime" page I tried returned 404, so I did not read how to plug in a plain `fetch`.
- Load for a learner (INFERENCE): high. The repo has 7,557 commits and many packages; use only the React core.

### B2. Vercel AI SDK UI (`useChat`, package `@ai-sdk/react`)
- What: a React hook that holds messages and streams assistant text into them. Not a set of visual components. [READ, VENDOR] [chatbot docs](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot), date unknown.
- Backend link: `DefaultChatTransport({ api })` sends an HTTP POST. Any server can answer if it emits the UI message stream (SSE, header `x-vercel-ai-ui-message-stream: v1`, ends with `data: [DONE]`). `TextStreamChatTransport` accepts plain text, but then there are no tool calls, usage or finish reasons. [READ, VENDOR] [chatbot docs](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot), [stream protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol).
- Lock-in (INFERENCE): medium for protocol, low for code. The text-only transport leaves the wire format free.
- The docs' server examples are Next.js. For non-JavaScript servers the docs point to the protocol page. [READ, VENDOR]

### B3. Vercel AI Elements (shadcn-style components)
- What: Conversation, Message, Prompt Input, Reasoning, Sources, Tool, and more, built on shadcn/ui. Repo says a Next.js project with the AI SDK is needed. 2.5k stars. [READ, VENDOR] [repo](https://github.com/vercel/ai-elements), [site](https://elements.ai-sdk.dev/).
- Warning on both pages: "This project will be deprecated at the end of November 2026" and moves into shadcn/ui. [READ, VENDOR] [site](https://elements.ai-sdk.dev/), date unknown. That is about a week from today.
- Fit (INFERENCE): do not start on it. Look at the shadcn/ui successor instead (not checked).

### B4. chatscope chat-ui-kit-react
- What: presentational components. The README example uses `MainContainer`, `ChatContainer`, `MessageList`, `Message`, `MessageInput`. Storybook has the full list; I could not read it (fetch returned only a title). A separate package `@chatscope/use-chat` holds state. [READ, VENDOR] [README](https://raw.githubusercontent.com/chatscope/chat-ui-kit-react/master/README.md), date unknown.
- Backend link: none. No networking, no wire format. You write the streaming code yourself. [READ for "UI-only as far as the README says"]
- Lock-in: low (INFERENCE). It does not render markdown by itself (README does not mention it); pair it with react-markdown.
- It has a conversation list component (from memory, unverified).

### B5. CopilotKit
- What: "Frontend stack for agents and generative UI", React, Angular and more. Creator of AG-UI; built on it. [READ, VENDOR] [repo](https://github.com/CopilotKit/CopilotKit)
- Fit (INFERENCE): it is built for agents that drive the app's own UI. That is more than a chat box needs. Lock-in to AG-UI, which is open (see C).

### B6. Markdown helpers
- react-markdown: MIT, 15.9k stars, "safe by default" (escapes HTML); suggests `rehype-sanitize` for stricter control. [READ, VENDOR] [repo](https://github.com/remarkjs/react-markdown)
- Streamdown (Vercel): "drop-in replacement for react-markdown designed for AI streaming". Apache-2.0, 5.8k stars. [READ] [repo](https://github.com/vercel/streamdown), [LICENSE](https://raw.githubusercontent.com/vercel/streamdown/main/LICENSE). Release date unknown.

### B7. Complete chat apps (references only)
- Too large to borrow from: Open WebUI (20,928 commits), LibreChat (7,051), LobeHub (16,700), Vercel `chatbot` (653 commits; Next.js, Postgres, Auth.js, Drizzle, CI). [READ, MEASURED] repo pages in section D. (INFERENCE on "too large": thousands of commits, own database layers, plugin systems.)
- Chainlit is a Python-first app framework with its own front end. It is now archived (see D, E).
- The Vercel `chatbot` template is the smallest of these. It is a good one to read for how a chat page, a conversation list and message storage fit together (INFERENCE), but its stack is Next.js, not plain React with FastAPI.

## C. Streaming from backend to browser

Takeaway: For one-way model output, Server-Sent Events (SSE) is the common default, and FastAPI 0.135+ supports it with no extra package. A plain streamed body (JSON Lines) is the simplest to read and debug. WebSocket is only needed if the same connection must carry data from browser to server during a reply. On the browser side, use `fetch` with a stream reader, not `EventSource`, because chat needs POST and an auth header.

### C1. Server-Sent Events (SSE)
- How: one long HTTP response with `Content-Type: text/event-stream`. Messages are text, ended by a blank line. The browser can reconnect and resume with `Last-Event-ID`. [READ, VENDOR (spec)] [WHATWG HTML standard, SSE section](https://html.spec.whatwg.org/multipage/server-sent-events.html), date unknown.
- FastAPI: built in since 0.135.0 (`fastapi.sse`, `EventSourceResponse`, `ServerSentEvent`). It sends a keep-alive ping every 15 seconds and sets `Cache-Control: no-cache` and `X-Accel-Buffering: no`. The page also covers `Last-Event-ID` and SSE over POST. [READ, VENDOR] [FastAPI SSE tutorial](https://fastapi.tiangolo.com/tutorial/server-sent-events/), date unknown. The 0.135.0 release date I could not find.
- Older route: `sse-starlette`, BSD-3-Clause, 859 stars, latest 3.7.1 on 2026-11-22, one maintainer (sysid), needs Python 3.11+. [READ, MEASURED] [PyPI](https://pypi.org/project/sse-starlette/), [repo](https://github.com/sysid/sse-starlette)
- React client: `EventSource` is simplest, but takes only a URL and `withCredentials`. [READ + SNIPPET] [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) (page last modified 2026-09-03); [DEV article](https://dev.to/ohugonnot/sse-with-fetch-readablestream-authenticated-streaming-without-eventsource-604) (EXPERIENCE, date unknown). That article says EventSource is GET only with no Authorization header [SNIPPET]. For POST and headers use `fetch` and read the body, or `@microsoft/fetch-event-source`. The repo is now at `Azure/fetch-event-source`: MIT, 2.9k stars, 20 commits, no archived banner. [READ] [repo](https://github.com/Azure/fetch-event-source), date unknown. Its upkeep I could not verify.
- Limits: over HTTP/1.1 browsers allow about 6 SSE connections per domain across tabs (MDN, READ). Proxy buffering and idle timeouts are the usual trouble (see E). Reconnect does not bring back missed tokens by itself. [READ] [Render article, 2026-10-28](https://render.com/articles/sse-vs-websockets-llm-streaming) (VENDOR, hosting company).
- Wire example (from MDN, READ, 2026-09-03):

```
: this is a test stream

data: some text

data: another message
data: with two lines
```

### C2. WebSocket
- How: the browser upgrades one HTTP connection to a two-way channel. Both sides can send at any time.
- FastAPI: built in through Starlette; needs the `websockets` package. Example uses `@app.websocket("/ws")` with `receive_text()` and `send_text()`. Auth uses a cookie or a `token` query parameter; raise `WebSocketException`. A connection manager in memory works for one process only. [READ, VENDOR] [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/), date unknown.
- React client: the native `WebSocket` object. It cannot set custom headers and has no auto-reconnect (Render article, READ, VENDOR). Render suggests a short-lived ticket instead of a token in the URL.
- Limits: some proxies and load balancers need extra setup for the upgrade [SNIPPET, VENDOR] [roundup of vendor blogs](https://render.com/articles/sse-vs-websockets-llm-streaming).
- Wire example: frames of text; for chat typically JSON such as `{"type":"delta","text":"Hel"}` (INFERENCE; not a published format).

### C3. Plain streamed body (JSON Lines, or NDJSON)
- How: one JSON object per line in a normal response, sent as it is produced.
- FastAPI: built in. Yield items from a path function; content type `application/jsonl`; added in 0.134.0. [READ, VENDOR] [FastAPI JSON Lines](https://fastapi.tiangolo.com/tutorial/stream-json-lines/). Raw `StreamingResponse` with `yield` also works for text and bytes [READ] [FastAPI stream data](https://fastapi.tiangolo.com/advanced/stream-data/).
- React client: `fetch(...)`, then `response.body.getReader()`, split on newline, `JSON.parse` each line (INFERENCE). Works with POST and any header.
- Limits: no built-in reconnect or event ids; same proxy buffering and compression issues as SSE (INFERENCE; consistent with Render article).
- Wire example (FastAPI docs, READ):

```
{"name": "Plumbus", "description": "A multi-purpose household device."}
{"name": "Portal Gun", "description": "A portal opening device."}
```

### C4. Message formats on top of the transport
- Vercel AI SDK UI message stream: SSE. Each event is `data: {json}`, then a blank line, ending with `data: [DONE]`. Header `x-vercel-ai-ui-message-stream: v1`. Chunk types include `start`, `text-start`, `text-delta`, `text-end`, `finish`, tool chunks and `data-*`. [READ, VENDOR] [stream protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol). Old v4 format was `TYPE_ID:JSON` lines with `x-vercel-ai-data-stream` [SNIPPET]. Example:

```
data: {"type":"text-delta","id":"msg_1","delta":"Hello"}
```
  (shortened from the page's example.)
- AG-UI (Agent-User Interaction protocol): event types such as RunStarted, TextMessageStart, TextMessageContent, TextMessageEnd, ToolCallStart, StateSnapshot, RunFinished. The events page names no transport. The repo says HTTP with SSE, plus a binary Protobuf binding, and has a Python SDK (`pip install ag-ui-protocol`). MIT, 21.4k stars, created by CopilotKit. [READ, VENDOR] [events](https://docs.ag-ui.com/concepts/events), [repo](https://github.com/ag-ui-protocol/ag-ui), dates unknown.
- OpenAI chat-completions chunk: `data: {"id":...,"object":"chat.completion.chunk",...,"choices":[{"delta":{"content":"Hello"}}]}` and a last line `data: [DONE]`. [READ, VENDOR] [OpenAI API reference](https://developers.openai.com/api/reference/resources/chat), date unknown. (The spec-style link is the reference page; I read only part of it.)
- assistant-transport (assistant-ui): SSE lines `data: {json}` ending `data: [DONE]`, or its older `aui-state:` lines. [READ, VENDOR] [docs](https://www.assistant-ui.com/docs/runtimes/custom/assistant-transport)
- Who expects what (READ for the first four, INFERENCE for the rest):
  - `useChat` expects the AI SDK UI message stream (or plain text with the text transport).
  - assistant-ui data-stream runtime expects the AI SDK UI message stream or its own data stream. It also has an AG-UI adapter package.
  - CopilotKit expects AG-UI.
  - chatscope and react-markdown expect nothing.
  - No component I read consumes the OpenAI chunk format directly. Provider libraries convert it (INFERENCE).

## D. License and maintenance state

Takeaway: Every item I could read is MIT, Apache-2.0 or BSD, except Open WebUI (BSD-style plus a branding clause) and LobeHub (Apache-based community license with limits on derivative works). Chainlit is Apache-2.0 but archived. AI Elements is about to be deprecated.

| Item | License (file) | Latest release or commit | Stars (rough) | Backing | Notes |
|---|---|---|---|---|---|
| full-stack-fastapi-template | MIT | commit 2026-11-16 | 46.3k | FastAPI creator | active |
| FastAPI | MIT | 0.165.0, 2026-11-18 | not collected | FastAPI creator | 0.x versions |
| Vite | MIT | v8.3.7 per docs, date unknown | not collected | VoidZero Inc. | |
| assistant-ui | MIT (AgentbaseAI Inc.) | releases daily, 2026-11-22 | 13.4k | company, "backed by Y Combinator" | optional paid cloud |
| Vercel AI SDK (`ai`) | Apache-2.0 | releases 2026-11-23 | 28.2k | Vercel | docs show v7 exists |
| Vercel AI Elements | Apache-2.0 | date unknown | 2.5k | Vercel | deprecation end Nov 2026 |
| Streamdown | Apache-2.0 | date unknown | 5.8k | Vercel | |
| Vercel `chatbot` template | Apache-2.0 | date unknown | 21.1k | Vercel | Next.js |
| CopilotKit | MIT (Atai Barkai) | v1.90.1, 2026-11-23 | 38.9k | CopilotKit company | |
| AG-UI | MIT (page) | date unknown | 21.4k | created by CopilotKit | |
| chatscope chat-ui-kit-react | MIT (page badge, README) | v2.1.1, 2025-05-15 | 1.8k | unnamed account | no release for 18 months |
| react-markdown | MIT | v10 line, date unknown | 15.9k | remarkjs org | |
| sse-starlette | BSD-3-Clause | 3.7.1, 2026-11-22 | 859 | one maintainer | |
| @azure/fetch-event-source | MIT (page) | date unknown | 2.9k | Azure org | upkeep unverified |
| LibreChat | MIT (file) | v0.8.9, 2026-11-17 | 47.5k | ClickHouse (bought it, 2025-11-04) | |
| Open WebUI | **Open WebUI License (flag)** | v0.13.4, 2026-11-17 | 159k | Open WebUI Inc. | branding clause |
| LobeHub (LobeChat) | **LobeHub Community License (flag)** | date unknown | 86.1k | LobeHub org | |
| Chainlit | Apache-2.0 | 2.12.0, 2026-08-25; archived 2026-10-15 | 12.5k | none now | read-only |
| ai-sdk-preview-python-streaming | license not verified | date unknown | 364 | Vercel Labs | demo |

Sources for the table (all READ unless noted; MEASURED): repo pages and `releases.atom` feeds for [fastapi](https://github.com/fastapi/fastapi/releases.atom), [assistant-ui](https://github.com/assistant-ui/assistant-ui/releases.atom), [vercel/ai](https://github.com/vercel/ai/releases.atom), [CopilotKit](https://github.com/CopilotKit/CopilotKit/releases.atom), [chatscope](https://github.com/chatscope/chat-ui-kit-react/releases.atom), [Open WebUI](https://github.com/open-webui/open-webui/releases.atom), [LibreChat](https://github.com/danny-avila/LibreChat/releases.atom), [Chainlit](https://github.com/Chainlit/chainlit/releases.atom). LICENSE files: [assistant-ui](https://raw.githubusercontent.com/assistant-ui/assistant-ui/main/LICENSE), [vercel/ai](https://raw.githubusercontent.com/vercel/ai/main/LICENSE), [CopilotKit](https://raw.githubusercontent.com/CopilotKit/CopilotKit/main/LICENSE), [LibreChat](https://raw.githubusercontent.com/danny-avila/LibreChat/main/LICENSE), [Open WebUI](https://raw.githubusercontent.com/open-webui/open-webui/main/LICENSE), [LobeHub](https://raw.githubusercontent.com/lobehub/lobehub/canary/LICENSE). Chainlit, chatscope, AG-UI, react-markdown and fetch-event-source licenses are from the repo page only (no raw file read).

Items that changed state:
- Open WebUI: code up to v0.6.5 is BSD-3-Clause. From v0.6.6 (2025-04-19, per the project's docs) a clause forbids changing "Open WebUI" branding, unless there are 50 or fewer users in 30 days, or you have written permission or an enterprise license. The project itself says it is "not an OSI-approved 'open source' license". Contributions need a CLA. [READ, VENDOR + MEASURED] [LICENSE](https://raw.githubusercontent.com/open-webui/open-webui/main/LICENSE), [docs](https://docs.openwebui.com/license/), [LICENSE_HISTORY](https://raw.githubusercontent.com/open-webui/open-webui/main/LICENSE_HISTORY).
- LobeHub: file says "LobeHub Community License", Apache 2.0 plus conditions; a commercial license is needed to distribute a derivative work. The README badge says Apache 2.0, which disagrees. [READ] [LICENSE](https://raw.githubusercontent.com/lobehub/lobehub/canary/LICENSE)
- LibreChat: ClickHouse acquired it, announced 2025-11-04; MIT stays; the founder joined ClickHouse. [SNIPPET, VENDOR + press] [Business Wire](https://www.businesswire.com/news/home/20251104505230/en/ClickHouse-Acquires-LibreChat-to-Democratize-AI-Driven-Analytics-Through-the-Open-Source-Agentic-Data-Stack). The LICENSE file now says "Copyright (c) 2026 LibreChat" (READ).
- Chainlit: the original team stepped back on 2025-05-01; the project became community-maintained. The repo page says: "This repository was archived by the owner on Oct 15, 2026. It is now read-only." [READ, MEASURED] [repo](https://github.com/Chainlit/chainlit). A search tool said it found no archive evidence, but its source was a record last synced 2026-04-08, so it is older than the archive date [SNIPPET].
- AI Elements: deprecation notice (see B3).

## E. Criticism and failure reports

Takeaway: Most real problems are not in the libraries but in the path between server and browser: proxy buffering, compression, idle timeouts, and the wire format that changes between major versions. License and maintenance risk is highest for Open WebUI, LobeHub, Chainlit and AI Elements.

- Open WebUI license change drew a mostly negative reaction: a thread titled "Open WebUI is no longer open source", a "red flag" post, and a comment that it is a heavier version of the old BSD advertising clause. Nixpkgs marks it non-free. [SNIPPET, EXPERIENCE] [search results incl. r/opensource thread, Nixpkgs commit](https://code.ornl.gov/nix/nixpkgs/-/commit/ac3ae15f554aadd84e29c7c0a73b9fa54f568721); Reddit mirrors, May 2025. I did not open the threads. Release-date sources disagree (2025-04-19 in the project docs; 2025-05-05 in one guide).
- Chainlit: archived about 5 months after its last release; the maintainers gave no reason on the pages I read. [READ, MEASURED] [repo](https://github.com/Chainlit/chainlit)
- Vercel AI SDK v5 broke message shapes and the `useChat` API: `content` became `parts`, and `useChat` moved to a transport design. Vercel gave codemods. One team wrote that history needed no database migration. [SNIPPET, VENDOR + EXPERIENCE] [migration guide](https://ai-sdk.dev/docs/migration-guides/migration-guide-5-0), [dev.to write-up](https://dev.to/web3nomad/how-we-migrated-atypicaai-to-ai-sdk-v5-without-breaking-10m-chat-histories-11lk). The wire format also changed from `TYPE_ID:JSON` lines (v4) to SSE JSON (v5+) [SNIPPET]. A Python backend must match the major version.
- Vercel AI SDK with FastAPI: an old issue reports the same streaming failure with FastAPI; commenters used a Next.js proxy route as a workaround. [SNIPPET, EXPERIENCE] [vercel/ai #161](https://github.com/vercel/ai/issues/161). It predates the current protocol. A Vercel forum thread reports a data stream response "getting cut off" [SNIPPET, EXPERIENCE] [thread](https://community.vercel.com/t/ai-sdk-data-stream-protocol-response-getting-cut-off/1316). I found no resolution.
- Lock-in: I found no direct lock-in complaint for the AI SDK. A rival's guide (TanStack) shows moving off it is mostly renaming packages and calls [SNIPPET, VENDOR (competitor)] [TanStack migration page](https://tanstack.com/ai/latest/docs/migration/migration-from-vercel-ai).
- assistant-ui: I found no complaint or issue report. Search returned only docs. Not looked at: its GitHub issue list. Weak evidence of absence.
- CopilotKit: reviews are secondary and thin. A comparison rates the learning curve "medium", hook complexity grows with features, and advises skipping it for a standalone chatbot. Cited pricing is for the vendor's hosted tiers, not the MIT code. [SNIPPET, EXPERIENCE/vendor comparison] [Speakeasy](https://www.speakeasy.com/blog/copilotkit-vs-openai-chatkit-vs-gram-elements), [MakerStack](https://makerstack.co/reviews/copilotkit-review/), both dates unknown.
- Starlette gzip: `GZipMiddleware` held back small streamed chunks, so SSE arrived late. Starlette PR #2871 ("Don't compress on server sent events") was merged 2025-02-16; the earlier flush PR #2753 was closed unmerged. [READ, MEASURED] [PR #2753](https://github.com/Kludex/starlette/pull/2753). Check your installed Starlette is newer. Compression can still hold tokens in other layers (Render article, READ).
- Nginx buffering: tokens arrive in batches unless buffering is off for that route; `X-Accel-Buffering: no` helps but one 2019 report and one Stack Overflow case say it did not, and `proxy_ignore_headers` can disable it. [SNIPPET, EXPERIENCE] [search roundup](https://oneuptime.com/blog/post/2025-12-16-server-sent-events-nginx/view), [nginx mailing list 2019](https://mailman.nginx.org/pipermail/nginx/2019-May/057864.html). `sse-starlette` README adds: Cloudflare buffers about 100 KB before flush; Akamai and F5 buffer by default; HAProxy timeouts must exceed the ping interval. [READ, VENDOR (maintainer)] [repo](https://github.com/sysid/sse-starlette)
- Cloudflare idle timeout article "the 125 second silence" (stream dies behind Cloudflare): [SNIPPET only; fetch returned 403] [link](https://levelup.gitconnected.com/the-125-second-silence-why-your-ai-stream-dies-behind-cloudflare-40f776d9e055). I could not read it, so I do not use its claims.
- Reconnect, idle timeouts and multi-server routing: a reconnect does not restore missed tokens. AWS ALB and nginx close idle connections at about 60 seconds by default, so send keep-alives (15 seconds). [READ, VENDOR (hosting company)] [Render, 2026-10-28](https://render.com/articles/sse-vs-websockets-llm-streaming)
- Full-stack template: I found no direct complaint about its size or learning curve. I searched the web for removal and migration problems and found none; I did not read its GitHub issues. That is weak evidence of absence. [SNIPPET]

## Summary table (every candidate)

| Name | Kind | License | Latest release/commit | Backing | Fit for a small learner-owned PoC (INFERENCE) |
|---|---|---|---|---|---|
| full-stack-fastapi-template | full-stack template | MIT | 2026-11-16 | FastAPI creator | Read, then cut down; too big to keep whole |
| create-vite (react-ts) | frontend starter | MIT | v8.3.7 (date unknown) | VoidZero | Good: small |
| FastAPI | backend framework | MIT | 2026-11-18 | FastAPI creator | Good; built-in SSE and JSON Lines |
| sse-starlette | SSE helper | BSD-3 | 2026-11-22 | one maintainer | Not needed on FastAPI 0.135+ |
| @azure/fetch-event-source | browser SSE client | MIT | date unknown | Azure org | Optional; plain `fetch` also works |
| assistant-ui | chat UI + runtime | MIT | 2026-11-22 | company (YC) | Good UI, heavy; format lock-in |
| Vercel AI SDK UI (`useChat`) | chat hook | Apache-2.0 | 2026-11-23 | Vercel | Fit if backend emits its stream; major-version churn |
| Vercel AI Elements | UI components | Apache-2.0 | date unknown | Vercel | Avoid: deprecation end Nov 2026 |
| chatscope chat-ui-kit-react | UI kit | MIT | 2025-05-15 | unnamed | Simple; you write streaming; slow upkeep |
| CopilotKit / AG-UI | agent UI + protocol | MIT / MIT | 2026-11-23 / date unknown | CopilotKit | Too much for plain chat; useful to know |
| react-markdown / Streamdown | markdown render | MIT / Apache-2.0 | date unknown | remarkjs / Vercel | Good, small |
| Open WebUI | full chat app | Open WebUI License (flag) | 2026-11-17 | Open WebUI Inc. | Reference only; do not borrow code |
| LibreChat | full chat app | MIT | 2026-11-17 | ClickHouse | Reference only; too large |
| LobeHub | full chat app | LobeHub Community License (flag) | date unknown | LobeHub | Do not borrow; ask owner |
| Chainlit | Python chat framework | Apache-2.0 | 2026-08-25; archived | none | Do not build on; archived |
| Vercel `chatbot` | full chat app | Apache-2.0 | date unknown | Vercel | Reference for structure; Next.js |
| ai-sdk-preview-python-streaming | demo | license not verified | date unknown | Vercel Labs | Read-only reference |

Only Open WebUI and LobeHub need an owner decision under the project rule. License not verified: ai-sdk-preview-python-streaming. The pages for Chainlit, chatscope, AG-UI, react-markdown and fetch-event-source gave the license from the repo page, not the raw file.

## What a small PoC could borrow (all INFERENCE; no choice made)

1. Minimal and plain: `create-vite` react-ts, own small chat page, `fetch` stream reader, FastAPI built-in SSE or JSON Lines, react-markdown. Cost: the owner writes the message list, input box and stream parsing (a few hundred lines). Everything is MIT or Apache; no wire-format lock-in. Most to learn, easiest to explain.
2. Plain core plus a UI kit: the same backend, but chatscope for the message list and input. Cost: you still write streaming and markdown; the kit's last release was 2025-05-15, so upkeep is slow; some styling work.
3. Hook-based: `useChat` (or assistant-ui) with a FastAPI endpoint that emits the AI SDK UI message stream. Cost: you must copy the protocol exactly (header and chunk types) and track major versions; the Python helper for assistant-ui is its own format. Saves UI and state code; adds a black box the owner must still understand.
4. (Optional add-on) Use the official full-stack template as a reading guide for sign-in and database layout, copying only small parts such as the user model and token check. Cost: understanding SQLModel, JWT and test setup; the rest of the template stays unused.

## Could not find or verify

- Commit dates for most repos: GitHub pages did not show them. I used release feeds where releases exist. For Vite, Streamdown, AI Elements, AG-UI, react-markdown, fetch-event-source, LobeHub, `chatbot`, and the template's releases, dates are unknown.
- Release date of FastAPI 0.135.0 (SSE) and 0.134.0 (JSON Lines): not in the feed page I read.
- Whether Chainlit's maintainers explained the Oct 2026 archive: not found. The only search source on archive state was stale.
- GitHub API calls returned 403, so exact star counts and "pushed_at" values come from page text only.
- The chatscope Storybook page, the assistant-ui "local runtime" page (404), and the Cloudflare idle-timeout article (403) were not read. I did not confirm chatscope's `ConversationList` component. The raw LICENSE for `ai-sdk-preview-python-streaming` returned 404.
- License of the `assistant-stream` package, chatscope's raw license file, and the AG-UI raw license: not read.
- The shadcn/ui replacement for AI Elements was not examined.
- I did not read the Open WebUI, Reddit or Hacker News threads, only search summaries. The claim of a 2026 "v0.9.0 condensed license text" came from one search summary and is unverified.
- Spec for the OpenAI chunk format: I read only the first part of the API reference page.
- Issue trackers (assistant-ui, CopilotKit, the template, chatscope) were not read. Criticism for them is therefore thin.
- No bash, so I did not run any code. No wire format was tested against a running server.

## Main agent's check (2026-11-23)
The main agent fetched five of this note's sources again. All five match the note.
- FastAPI SSE tutorial: `from fastapi.sse import EventSourceResponse, ServerSentEvent`, "Added in FastAPI 0.135.0", a keep-alive ping every 15 seconds, `Cache-Control: no-cache` and `X-Accel-Buffering: no` set automatically, and an SSE example on a POST route.
- Chainlit repository page: "This repository was archived by the owner on Oct 15, 2026. It is now read-only." License Apache-2.0.
- Open WebUI raw LICENSE: BSD-3-Clause text plus a fourth clause on "Open WebUI" branding, with the exception for 50 or fewer end users in a rolling 30 days.
- Vercel AI SDK stream protocol page: SSE, header `x-vercel-ai-ui-message-stream: v1`, `text-delta` chunks, `data: [DONE]` at the end, and a statement that a backend in another language such as Python can implement it.
- AI Elements site: "AI Elements is moving to shadcn/ui. This project will be deprecated at the end of November 2026."
