# Trial runs of the Copilot SDK (2026-11-23 and 2026-11-27)

The main agent ran these trials in a session's sandbox container. The owner agreed to each in conversation. Dates and times are US Eastern Time unless a log line says otherwise.

There are four runs. The first two use a local stand-in for the model provider and no model key. The third calls a real model. It is under "Third run: a real model provider". The fourth, on 2026-11-27, runs the finished product in a browser with the model from configuration. It is under "Fourth run: the product in a browser, with the real model".

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
- The privacy center page also says "for Covered Models, we require limited data retention and review as a part of our safety work." The API and data retention page lists the Covered Models. `claude-opus-5-5` is not on that list.

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
   - First turn, among other events: 16 `assistant.reasoning_delta`, 7 `assistant.message_delta`, one `assistant.message`, one `assistant.reasoning`, then `session.idle`. The reasoning events carry a summary of the model's thinking. The first reasoning piece arrived before the first text piece.
   - Second turn, among other events: no reasoning events, 3 `assistant.message_delta`, one `assistant.message`, then `session.idle`.
   - Each turn also brought `assistant.streaming_delta` events (23 and 3) and 9 events that the Python SDK reported as type "unknown".
   - A chat interface must decide what to do with the reasoning events: show them, or ignore them.
4. Timing, as the runtime recorded it.
   - First turn: 3.0 seconds in total. The first piece arrived after 3.0 seconds. The reasoning pieces and the text pieces all arrived within about 12 milliseconds at the end. So the user would see nothing for 3 seconds and then the whole answer at once.
   - Second turn: 1.2 seconds in total. The first piece arrived after 0.6 seconds.
   - `client.start()` took 0.04 seconds and `create_session` took 0.23 seconds.
5. Tokens and cost.
   - First turn: 95 input tokens, 113 output tokens. 83 of the output tokens were reasoning.
   - Second turn: 257 input tokens, 13 output tokens. The request body grew from 622 to 2,237 bytes. The input most likely grew because the history is sent again, including the reasoning block of the first turn. This is an inference: the body of the real second request was not recorded. It is supported by a replay of the stored conversation against the stand-in. There the runtime sent the first assistant message with that block: 178 characters of reasoning text and a signature of 1,100 characters.
   - Total: 352 input and 126 output tokens. At $4 and $20 per million tokens for Claude Opus 5.5, that is about $0.004. Prices from the vendor's [pricing page](https://platform.claude.com/docs/en/about-claude/pricing), read 2026-11-23.
   - The runtime reports `cost: 0.0` for a BYOK provider. The application must work out cost from the token counts.
   - The cache counts were 0 in both turns. The likely reason is that the prompt is shorter than the provider's minimum for caching. This is an inference and was not checked.
   - The runtime's limits for this model: 128,000 prompt tokens and 48,000 output tokens.
6. What is stored on disk. `events.jsonl` held 15 events as plain text:
   - the user's text in two forms, as typed and with the date line added;
   - the system prompt;
   - the assistant's text;
   - the summary of the model's reasoning, and an opaque reasoning block. The replay showed that the runtime sends this block back with the history;
   - usage records with token counts and timings;
   - the working directory of the process.
   - The key was in none of the files.
   - `get_events()` returned 6 events after the first turn, among them the user message and the assistant message.
   - A later check on a copy of the stored files, with no message sent: after a resume, `get_events()` returned the first assistant message with its reasoning summary in the field `reasoning_text`, 176 characters. The second assistant message, which had no reasoning, came with that field empty. So an interface can read the reasoning of old messages through the SDK.
7. Outside connections during the real run, about five seconds:
   - one TCP connection to `160.79.104.10` port 443. A lookup of `api.anthropic.com` made less than a minute before the run returned this address. The lookup inside the run was not recorded. There was only one such connection, so both requests presumably used it;
   - one DNS socket to `8.8.8.8` port 53, a public DNS server. The names asked for were not recorded;
   - four attempts to reach the local name service socket `/var/run/nscd/socket`. All failed because the socket does not exist. It is not a network connection;
   - nothing through the logging proxy.
   - So apart from the DNS lookup, the only outside connection was to the provider's address. As before, this covers a short run with no errors.
8. `get_auth_status()` returned "Not authenticated", as in the first run. So a real provider also works with no GitHub sign-in.
9. Memory of the Python process: 77 MB before start, 130 MB after `client.start()`, 163 MB with one session, 185 MB at the end.

### What this changes

- "A real model provider" moves from "not tested" to "worked in one run, with Anthropic and one model".
- Two closed Anthropic BYOK bugs from the basics note did not appear in this run. The message, reasoning and idle events arrived (issue #1064, known by its title only). The output limit sent was 48,000 and not 8,192 (issue #955). Whether cache counts are filled (issue #1073) could not be judged, because both counts were 0. Compaction (issue #1072) was not tested.
- New: the runtime turns on thinking, an effort level and prompt caching by itself.
- New: with a real model the first answer can arrive all at once after a wait, even with streaming on.
- New: the stored file keeps the summary of the model's reasoning next to the messages.
- New: the SDK does not work out cost under BYOK.

## Fourth run: the product in a browser, with the real model (2026-11-27)

This is task 8 of the first PoC. The owner chose that the main agent drives the browser in the cloud session, and that the run covers a question, a follow-up and four more things: a long answer with Markdown, a message in Chinese, "Stop" during an answer, and a backend with a made-up key. The model is the one from configuration, `claude-haiku-5-5`. No earlier run had used it.

### Method

- A cloud session on the project environment `AI-Articheture-Research`, which holds the key in the variable `POC_MODEL_API_KEY`. Linux x86_64, Python 3.13.18, `microsoft-copilot-sdk==2.0.1`, runtime 1.0.114, Node 22, Playwright 1.63.0 with the Chromium of the session, without a window.
- Part 1, a dry run with no real key. A trial script makes a session with the same options as `backend/app/agent.py`, resumes it and sends one message, as the product does. A "variant" adds session options to these. The requests go to the stand-in of the tests, `backend/tests/model_stand_in.py`, which records them. The script takes the real key out of its process before anything starts. The purpose is to see what the runtime sends before anything real is sent.
- Part 2, the product in a browser. The product as it is on `main`, with no change. The backend runs under uvicorn with the real key and calls the provider's address directly. The page runs on the development server of the frontend. The database file and the session folder are in a scratch folder. A Playwright script signs in as a throwaway user and sends six messages in two conversations. It notes the time of every change of the page, takes screenshots and records a video. The token counts of this part come from the usage records that the runtime writes into the session files.
- Part 3, the settings with the real model. The same trial script as in part 1. Between the runtime and the provider stands a small local forwarder, which is part of the script. It passes each request on to the provider's address and records the request and the events of the answer with their times. So this part shows the real request and the provider's own token counts.
- The key. No script prints it. The forwarder leaves the key header out of what it records. After the run, two searches looked for the key in files. They are under "Results".
- The first attempt of part 2 stopped after four messages, through a fault of the script and not of the product. The script wrote the next message into the text box while the page was still changing to the new conversation. The page makes a new chat view for each conversation, so the text was gone and "Send" stayed switched off. The script now waits until the new conversation is shown. A person cannot type that fast. The four messages of the first attempt called the real model too, and their token counts are in the totals below.
- All of this is evidence of the kind "measured data, one run on one machine, one model". Unless a line says otherwise, each number comes from one request.

### Results

1. It worked. Every message in the browser got a streamed answer from the real model, and the page showed no error. The console of the browser held no error. The log of the backend held no error.

   | Message | First text on the page | Answer complete on the page | Input tokens | Output tokens | Of these, reasoning | Request body |
   |---|---|---|---|---|---|---|
   | 1. "What is the capital of Australia? Answer in one sentence." | 0.62 s | 0.83 s | 137 | 15 | 0 | 786 bytes |
   | 2. "Roughly how many people live in that city? One sentence." | 1.61 s | 1.83 s | 204 | 144 | 112 | 1,062 bytes |
   | 3. A guide to making tea, with a heading, a numbered list, a code block and a table | 0.66 s | 2.96 s | 449 | 531 | 0 | 2,937 bytes |
   | 4. A question in Chinese about Server-Sent Events | 0.50 s | 1.36 s | 1,047 | 134 | 0 | 4,487 bytes |
   | 5. "Write a detailed essay of about 1500 words on the history of the bicycle." Stopped by hand | 7.19 s | stopped after about 9.4 s | no record | no record | no record | no record |
   | 6. "In one sentence: what have I asked you for so far in this conversation?" | 1.47 s | 1.83 s | 197 | 111 | 79 | 969 bytes |

   - Messages 1 to 4 are one conversation. Messages 5 and 6 are a second one.
   - The times are measured on the page, from the click on "Send". The token counts and the body sizes are what the runtime stored in the session files.
   - Answer 2 used answer 1: "Canberra has roughly 460,000 to 480,000 residents, based on recent estimates." So the history reaches the real model.
   - The line "The model is working…" was on the page 0.03 to 0.05 seconds after the click, in every turn.
2. What the runtime sends for this model. Seen in the dry run and again in part 3, where the body was the same, 814 bytes.
   - `POST /v1/messages`. Headers, among others: `anthropic-version: 2023-06-01`, `anthropic-beta: thinking-binding-controls-2026-08-01`, `user-agent: Anthropic/JS 0.94.0`. The third run saw a second name in the beta header. It is not there with this model.
   - Body settings: `max_tokens: 128000`, `temperature: 1`, `thinking: {"type": "adaptive", "display": "summarized", "block_binding": {"prefix_mismatch_behavior": "drop_block"}}`, `output_config: {"effort": "medium"}`, `stream: true`. There is no list of tools.
   - The output limit is 128,000 tokens. For `claude-opus-5-5` in the third run it was 48,000. So the runtime seems to pick the limit by the model name. This is an inference from two models.
   - The system prompt is exactly the text of the product, with a prompt-cache marker. The user message has the `<current_datetime>` line in front and a prompt-cache marker, as in the third run.
   - The body of a request that the product sent directly to the provider was not seen. The runtime's own record gives its size: 786 bytes for message 1. The dry-run request was 814 bytes, and its message was 28 characters longer. So the two have the same shape. This is an inference from the sizes.
3. Which of these settings the application can change. Each row is one variant of the trial script. "Sent" is what the request then held, seen at the stand-in and, where the last column has an answer, also at the forwarder.

   | Session option | Sent | The real provider |
   |---|---|---|
   | none (the product today) | `effort: "medium"`, `max_tokens: 128000`, `display: "summarized"` | answered |
   | `inference.reasoning_effort: "low"` | `effort: "low"` | answered |
   | `inference.reasoning_effort: "high"` | `effort: "high"` | answered |
   | `inference.reasoning_effort: "xhigh"`, and `"max"` | `effort: "xhigh"`, and `"max"` | not sent |
   | `inference.reasoning_effort: "none"` | `effort: "low"`. Thinking stays "adaptive" | not sent |
   | `inference.reasoning_effort: "banana"`, a made-up value | `effort: "high"`, with no error | not sent |
   | `inference.reasoning_summary: "none"` | `display: "omitted"` | answered |
   | `inference.reasoning_summary: "detailed"` | no change | not sent |
   | `inference.models` with one entry for the model and `max_output_tokens: 2000` | `max_tokens: 2000` | answered |
   | the same limit, given in `capabilities.limits` of that entry | `max_tokens: 2000` | not sent |
   | `capabilities.supports.adaptive_thinking: "required"` or `"optional"`, with `reasoning_effort: "none"` | `thinking: {"type": "disabled"}`, `temperature: 0`, no `output_config` | refused with status 400: "`temperature` is deprecated for this model." Sent once, with "required" |
   | `capabilities.supports.adaptive_thinking: "unsupported"`, together with `capabilities.supports.reasoning_effort: false` | `thinking: {"type": "enabled", "budget_tokens": 2048, …}`, no `output_config` | refused with status 400: "\"thinking.type.enabled\" is not supported for this model." |
   | `capabilities.supports.reasoning_effort: false` alone | no change | not sent |

   - Effort: the application can set it. The one value that the SDK did not know, "banana", was not refused: the request held "high".
   - Output limit: the application can set it, with an entry in `inference.models`. See result 4 for what happens when an answer reaches the limit.
   - Reasoning summary: the application can switch it off. The model still thinks, and the thinking is still paid for. With a question that needs thought, the request with `display: "omitted"` used 700 thinking tokens, and the request with the summary used 689. With "omitted" the SDK gave no reasoning events at all.
   - Thinking itself: no way was found to switch it off for this model with SDK 2.0.1. The two ways that the options offer both end in a refusal by the provider. With effort "low" the model did not think in either of the two requests that tried it.
   - These are options of a session. The product would give them in the function `_inference` of `backend/app/agent.py`, on every create and resume. The product was not changed.
4. An answer that reaches the output limit. One request with a limit of 150 tokens and the message "Write about 300 words on why the sky is blue."
   - The provider ended the answer with the stop reason "max_tokens". The runtime then sent a second request by itself, with one more user message: "Please continue from where you left off." That answer hit the limit too, and the runtime sent a third request of the same kind. Then it ended the turn with `session.idle` and no error event.
   - The three requests used 901 input tokens and 450 output tokens, of which 413 were thinking. The turn took 6.1 seconds.
   - What a reader got: 88 characters, a heading and one sentence. Nothing marks the answer as cut.
   - So a low limit does not stop a turn at one request, and it can leave little room for the visible answer, because thinking counts against the same limit.
5. Timing.
   - With no thinking, the first text was on the page after 0.5 to 0.7 seconds (messages 1, 3 and 4). With some thinking, after about 1.5 seconds (messages 2 and 6, with 112 and 79 reasoning tokens).
   - The product's own path costs little. The first text was on the page 0.10 to 0.23 seconds later than the time to the first token in the runtime's record. The path is browser, development server, backend, the resume of the session, and back.
   - A long answer arrives in many small steps. Answer 3, 531 output tokens, grew on the page 107 times in 2.2 seconds. The chat stayed scrolled to its bottom.
   - The longest wait was that of message 5: the first text came after 7.2 seconds. Its cause was not measured. The turn was stopped, so it has no usage record and no count of thinking tokens. That the model thought during those seconds is an inference from the next point.
   - Thinking makes the wait long. This was measured at the forwarder in part 3, with the message "I have a 3-litre jug and a 5-litre jug and a tap. Describe the shortest way to measure exactly 4 litres, as numbered steps." One request for each row:

     | Setting | Output tokens | Of these, thinking | First reasoning piece | First text | End |
     |---|---|---|---|---|---|
     | effort "medium" (the product today) | 989 | 689 | 1.42 s | 4.97 s | 4.99 s |
     | effort "medium", summary off | 996 | 700 | none | 3.36 s | 4.30 s |
     | effort "low" | 346 | 0 | none | 0.43 s | 1.85 s |

   - In the first row the SDK gave 67 reasoning pieces between 1.4 and 5.0 seconds, and then the whole text, 603 characters, within 0.02 seconds. So when the model thinks for seconds, the reasoning summary does arrive during the wait. In the third run it had arrived together with the answer, but that answer needed only 83 reasoning tokens.
   - The model decides for each request whether it thinks. The short message of part 3, "A farmer has 17 sheep. All but 9 run away. How many are left? Answer in one sentence.", was sent twice with effort "medium" and the summary on. The two requests differed only in the output limit. The answer with the limit of 128,000 tokens had 29 thinking tokens and took 1.14 seconds. The answer with the limit of 2,000 had none and took 0.50 seconds. With effort "high" the answer had 29 thinking tokens, with "low" none.
6. Tokens and cost.
   - At least 24 requests reached the provider. 20 were answered: 9 in the browser, in both attempts together, and 11 through the forwarder. One was stopped by hand. Three were refused: two with status 400 in part 3 and one with 401 for the made-up key. How many requests the runtime sent for the made-up key was not seen.
   - The 20 answered requests used 5,954 input tokens and 4,738 output tokens. 2,121 of the output tokens were thinking.
   - Prices for Claude Haiku 5.5, for prompts up to 100,000 tokens: $0.10 for a million input tokens, $0.125 for a million tokens written to the 5-minute cache, $0.01 for a million tokens read from the cache, $0.50 for a million output tokens. Thinking is paid as output. From the vendor's [pricing page](https://platform.claude.com/docs/en/about-claude/pricing), read 2026-11-27. A request with a prompt over 100,000 tokens costs five times as much.
   - At these prices the 20 answered requests cost about $0.003. The stopped answer is not in this number. That the three refused requests cost nothing is an assumption and was not checked.
   - The history is sent again with every message. In the first conversation the input grew from 137 to 204, 449 and 1,047 tokens over four messages, and the body from 786 to 4,487 bytes.
   - The prompt cache. In the first three messages the cache counts were 0. In message 4 the runtime's record shows 1,047 input tokens and 1,043 tokens written to the cache. The first attempt showed the same: 1,010 and 1,006. In both conversations the first write to the cache came with the fourth message, when the prompt had passed 1,000 tokens. The likely cause is the length of the prompt: in this run the change lies somewhere between 449 and 1,010 tokens. This is an inference. It fits the inference of the third run, that its prompts were too short. No request read from the cache: no fifth message was sent. That the 1,047 input tokens of the record include the 1,043 is an inference, from adding up the turn before.
   - The runtime reports `cost: 0.0` again. Its usage record has what a cost needs: the input, output, reasoning and cache counts of each request.
   - The session files hold one usage record, of the type `session.usage_record`, for each answered request. For the stopped answer there is none: the file holds an event of the type `abort` with the reason "user_initiated" and no token counts. So the application cannot learn from the session files how many tokens a stopped answer used.
   - The record names `reasoningSummary: "detailed"`, while the request says `display: "summarized"`. The record names the limits that the runtime uses for this model: 128,000 prompt tokens and 128,000 output tokens.
7. The four more things in the browser.
   - Markdown. The page drew the heading, the numbered list and the code block of answer 3. The model wrote the table in the usual Markdown form with bars, and the page showed it as plain text with bars. This is the known limit of task 7: the page has no add-on for tables.
   - Chinese. The model answered the Chinese question in Chinese, in three sentences. The answer grew on the page 33 times.
   - "Stop". The script pressed it about two seconds after the first text of answer 5. The time of the click itself was not recorded. The answer last grew 9.35 seconds after "Send", with 1,733 characters on the page, and the page took a new message 0.06 seconds after that. The page showed "The answer was stopped." The text of the stopped answer left the page: the history held the question with no answer, also after a reload. Answer 6 named the essay: "You asked me to write a detailed essay of about 1,500 words on the history of the bicycle." So the stopped message stays in what the model sees.
   - A made-up key. A second backend got a key that the launch script made up. The page showed "The answer could not be completed. Try again later." 0.36 seconds after the click. The log of the backend held the cause: the provider's status 401, in a text of the runtime. That text tells the reader to check `COPILOT_PROVIDER_API_KEY` and two more variables of the runtime. The product does not use them: its variable is `POC_MODEL_API_KEY`. In task 4, against the stand-in, the runtime tried a 401 again for about two seconds. Here the whole refusal took 0.36 seconds.
   - After a reload the second conversation was open again, with two messages of the user and one answer. The list showed both titles, the later conversation first.
8. The key is in no file. After the run, a script read the key from the variable and looked for it, without printing it.
   - In the scratch folder of the trial, with every record, log, session file, screenshot and the video, and in the working copy of the repository, without the installed packages: 368 files, the key in none.
   - In every file under `/root`, `/tmp`, `/var/tmp`, `/home` and `/var/log` that had changed in the two hours before the search, again without the installed packages: 2,222 files, the key in none.
   - The screenshots and the video were shown to the owner in the conversation. They are not kept in the repository.

### What this changes

- The model from configuration works through the SDK and the product. Until now only `claude-opus-5-5` had been tried.
- "Whether the application can change the settings the runtime chooses" moves from "not tested" to: effort, the output limit and the reasoning summary can be changed with session options. Thinking cannot be switched off for this model. Effort "low" is the nearest thing.
- New: the runtime answers a reached output limit by asking the model to continue, up to three requests in this run, and then ends the turn with no error.
- New: when the model thinks for long, the first text takes seconds: 5.0 seconds in the one request where this was measured. The reasoning summary arrives during that wait. This speaks for task 9, which shows it. Three of the five answers in the browser had no reasoning at all.
- New: the session files hold the token counts of every answered request, and none for a stopped answer.
- New: in this run the prompt cache started to work by itself when a conversation had grown to about 1,000 tokens.

### Limits of this run

- One request for each point. The timings are single numbers, not averages.
- The body of a request from the product itself was not seen, only its size.
- No request read from the prompt cache.
- The settings were tried with the trial script, not through the code of the product.
- The outside connections of the runtime were not recorded this time.

## Not tested

- Latency over many runs. Answers of many thousands of tokens. A rate limit of the provider. Providers other than Anthropic, and models other than `claude-opus-5-5` and `claude-haiku-5-5`. The open BYOK bugs listed in the basics note.
- A request that reads from the prompt cache. Changing or turning off the caching settings that the runtime chooses. The effort values "xhigh" and "max" with a real model.
- A long conversation: the time of a resume, the growth of the cost, and what the runtime does when the history no longer fits.
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

## The trial scripts of the fourth run

The fourth run used the scripts below. They are throwaway experiments and not project code. They ran from a scratch folder outside the repository.

- `settings_trial.py` is part 1 and part 3: the session options, against the stand-in or through the forwarder. It ran from `backend/`, with `PYTHONPATH=.` so that it finds the settings class of the product. The variable `TRIAL_PROMPT` gives another message.
- `start_product.sh` and `stop_product.sh` start and stop the backend and the page for part 2.
- `browser_run.js` is part 2: it drives the page.
- Four more scripts of under 50 lines each are not printed. One prints a summary of the records. One reads the usage records from the session files. Two look for the key in files: they read the key from the variable, search the bytes of each file, and print the number of files searched and the names of files that hold the key. One of the two also adds up the tokens.

```python
"""Trial of the request settings that the runtime of the Copilot SDK chooses,
and of the session options that may change them.
Throwaway experiment. Not project code.

Run from backend/:
  uv run --no-sync python <this file> <target> <output folder> <variant> [...]

  target "stand-in": requests go to the local stand-in of the tests. The real
                     key is taken out of the process first.
  target "real":     requests go through a local forwarder to the real
                     provider. The forwarder records each request and the
                     events of the answer. It never records the key.

The model name, the provider type, the provider's address and the system
prompt come from the settings class of the product, so the trial uses the
model from configuration. Each variant makes a session with the options of
backend/app/agent.py plus the options of the variant, then resumes it and
sends one message, as the product does.
"""

import asyncio
import json
import os
import secrets
import sys
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
from copilot import CopilotClient, RuntimeConnection
from copilot._generated.rpc import (
    AdaptiveThinkingSupport,
    ModelCapabilitiesOverride,
    ModelCapabilitiesOverrideLimits,
    ModelCapabilitiesOverrideSupports,
)
from copilot.rpc import PermissionDecisionReject

LABEL = "provider"
PROMPT = os.environ.get(
    "TRIAL_PROMPT",
    "A farmer has 17 sheep. All but 9 run away. How many are left? "
    "Answer in one sentence.",
)
SECRET_HEADERS = {"x-api-key", "authorization", "cookie", "proxy-authorization"}


def caps(thinking: str | None, effort: bool | None = None) -> ModelCapabilitiesOverride:
    return ModelCapabilitiesOverride(
        supports=ModelCapabilitiesOverrideSupports(
            adaptive_thinking=AdaptiveThinkingSupport(thinking) if thinking else None,
            reasoning_effort=effort,
        )
    )


def variants(model: str) -> dict[str, dict]:
    no_thinking = ModelCapabilitiesOverride(
        supports=ModelCapabilitiesOverrideSupports(
            adaptive_thinking=AdaptiveThinkingSupport.UNSUPPORTED,
            reasoning_effort=False,
        )
    )
    small_limit = ModelCapabilitiesOverride(
        limits=ModelCapabilitiesOverrideLimits(max_output_tokens=2000)
    )
    return {
        "baseline": {},
        "effort_low": {"reasoning_effort": "low"},
        "effort_high": {"reasoning_effort": "high"},
        "effort_none": {"reasoning_effort": "none"},
        "summary_none": {"reasoning_summary": "none"},
        "summary_detailed": {"reasoning_summary": "detailed"},
        "limit_2000": {
            "models": [{"id": model, "provider": LABEL, "max_output_tokens": 2000}]
        },
        "caps_limit_2000": {
            "models": [{"id": model, "provider": LABEL, "capabilities": small_limit}]
        },
        "caps_no_thinking": {
            "models": [{"id": model, "provider": LABEL, "capabilities": no_thinking}]
        },
        "effort_xhigh": {"reasoning_effort": "xhigh"},
        "effort_max": {"reasoning_effort": "max"},
        "effort_made_up": {"reasoning_effort": "banana"},
        "required_none": {
            "reasoning_effort": "none",
            "models": [{"id": model, "provider": LABEL, "capabilities": caps("required")}],
        },
        "optional_none": {
            "reasoning_effort": "none",
            "models": [{"id": model, "provider": LABEL, "capabilities": caps("optional")}],
        },
        "no_effort_support": {
            "models": [{"id": model, "provider": LABEL, "capabilities": caps(None, False)}]
        },
        "limit_150": {
            "models": [{"id": model, "provider": LABEL, "max_output_tokens": 150}]
        },
        "low_and_limit": {
            "reasoning_effort": "low",
            "models": [{"id": model, "provider": LABEL, "max_output_tokens": 2000}],
        },
    }


class Forwarder:
    """Passes each request on to the real provider and records what passes."""

    def __init__(self, upstream: str) -> None:
        self.upstream = upstream.rstrip("/")
        self.requests: list[dict] = []
        forwarder = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: object) -> None:
                pass

            def do_POST(self) -> None:
                raw = self.rfile.read(int(self.headers.get("content-length", "0")))
                record: dict = {
                    "method": "POST",
                    "path": self.path,
                    "headers": {
                        k.lower(): v
                        for k, v in self.headers.items()
                        if k.lower() not in SECRET_HEADERS
                    },
                    "body_bytes": len(raw),
                    "body": json.loads(raw) if raw else None,
                    "answer": {"events": [], "usage": {}},
                }
                forwarder.requests.append(record)
                answer = record["answer"]
                # The key travels on in its header and is written nowhere.
                headers = {
                    k: v
                    for k, v in self.headers.items()
                    if k.lower() not in {"host", "content-length", "accept-encoding"}
                }
                headers["accept-encoding"] = "identity"
                started = time.monotonic()
                with (
                    httpx.Client(timeout=httpx.Timeout(180, connect=20)) as http,
                    http.stream(
                        "POST", forwarder.upstream + self.path, headers=headers, content=raw
                    ) as response,
                ):
                    answer["status"] = response.status_code
                    answer["seconds_to_status"] = round(time.monotonic() - started, 3)
                    self.send_response(response.status_code)
                    for name in ("content-type", "request-id", "retry-after"):
                        if name in response.headers:
                            self.send_header(name, response.headers[name])
                    self.send_header("Connection", "close")
                    self.end_headers()
                    rest = b""
                    error_text = b""
                    for chunk in response.iter_raw():
                        self.wfile.write(chunk)
                        self.wfile.flush()
                        if response.status_code != 200:
                            error_text += chunk
                            continue
                        rest += chunk
                        *lines, rest = rest.split(b"\n")
                        for line in lines:
                            if line.startswith(b"data:"):
                                note_event(
                                    answer, json.loads(line[5:]), time.monotonic() - started
                                )
                    if error_text:
                        answer["error_body"] = error_text.decode("utf-8", "replace")[:800]
                    answer["seconds_total"] = round(time.monotonic() - started, 3)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self.address = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()


def note_event(answer: dict, event: dict, seconds: float) -> None:
    kind = event.get("type")
    if kind == "message_start":
        answer["usage"].update(event["message"].get("usage", {}))
        answer["model"] = event["message"].get("model")
    elif kind == "message_delta":
        answer["usage"].update(event.get("usage", {}))
        answer["stop_reason"] = event.get("delta", {}).get("stop_reason")
    elif kind == "content_block_start":
        kind = "start:" + event["content_block"]["type"]
    elif kind == "content_block_delta":
        delta = event["delta"]
        kind = delta["type"]
        size = len(delta.get("text", "") or delta.get("thinking", ""))
        answer.setdefault("characters", Counter())[kind] += size
    answer["events"].append([round(seconds, 3), kind])


def reject(request: object, invocation: object) -> object:
    return PermissionDecisionReject(feedback="This trial allows no tools.")


def plain(value: object) -> object:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


async def run_variant(client, settings, base_url, key, extra) -> dict:
    result: dict = {"sdk_events": {}, "usage_events": []}
    session_id = secrets.token_hex(16)

    def options() -> dict:
        provider = {
            "name": LABEL,
            "type": settings.model_provider_type,
            "base_url": base_url,
            "api_key": key,
        }
        return dict(
            model=settings.model_name,
            system_message={"mode": "replace", "content": settings.system_prompt},
            permissions={"on_request": reject},
            inference={"default_provider": LABEL, "providers": [provider], **extra},
            tools={"available_tools": []},
            github={"capi": {"enabled": False}},
            events={"streaming": True},
        )

    try:
        session = await client.create_session(
            session_id=session_id, name=session_id, **options()
        )
        await session.disconnect()
        session = await client.resume_session(session_id, **options())
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"[:600]
        return result

    loop = asyncio.get_running_loop()
    done = asyncio.Event()
    seen: Counter = Counter()
    marks: dict[str, float] = {}
    texts: list[str] = []
    reasoning: list[str] = []
    started = time.monotonic()

    def receive(event) -> None:
        kind = event.type.value if hasattr(event.type, "value") else str(event.type)
        seen[kind] += 1
        marks.setdefault(kind, round(time.monotonic() - started, 3))
        if kind == "assistant.message_delta":
            texts.append(event.data.delta_content)
        elif kind == "assistant.reasoning_delta":
            reasoning.append(getattr(event.data, "delta_content", "") or "")
        elif kind in ("assistant.usage", "session.error"):
            result["usage_events"].append({kind: plain(event.data)})
        if kind in ("session.idle", "session.error"):
            loop.call_soon_threadsafe(done.set)

    session.on(receive)
    await session.send(PROMPT)
    try:
        await asyncio.wait_for(done.wait(), timeout=150)
    except TimeoutError:
        result["error"] = "no session.idle within 150 seconds"
    result["seconds_total"] = round(time.monotonic() - started, 3)
    result["sdk_events"] = dict(seen)
    result["first_seen_after_seconds"] = {
        kind: marks[kind]
        for kind in ("assistant.reasoning_delta", "assistant.message_delta", "session.idle")
        if kind in marks
    }
    result["answer_text"] = "".join(texts)
    result["reasoning_summary_text"] = "".join(reasoning)
    await session.disconnect()
    return result


async def main() -> None:
    target, out, *names = sys.argv[1:]
    out_folder = Path(out)
    out_folder.mkdir(parents=True, exist_ok=True)
    real_key = os.environ.get("POC_MODEL_API_KEY", "")

    if target == "stand-in":
        # The real key leaves the process before anything starts.
        os.environ.pop("POC_MODEL_API_KEY", None)
        real_key = ""
        sys.path.insert(0, "tests")
        from model_stand_in import ModelStandIn

        stand_in = ModelStandIn()
        stand_in.start()
        base_url, key = stand_in.address, "trial-" + secrets.token_urlsafe(24)

        def take_requests() -> list[dict]:
            taken = [
                {
                    "method": r.method,
                    "path": r.path,
                    "headers": {
                        k.lower(): v
                        for k, v in r.headers.items()
                        if k.lower() not in SECRET_HEADERS
                    },
                    "body_bytes": len(json.dumps(r.body, separators=(",", ":"))),
                    "body": r.body,
                }
                for r in stand_in.requests
            ]
            stand_in.requests.clear()
            return taken
    else:
        from app.config import Settings as RealSettings

        forwarder = Forwarder(RealSettings().model_provider_address)
        base_url, key = forwarder.address, real_key

        def take_requests() -> list[dict]:
            taken = list(forwarder.requests)
            forwarder.requests.clear()
            return taken

    from app.config import Settings

    settings = Settings()
    all_variants = variants(settings.model_name)
    client = CopilotClient(
        mode="empty",
        runtime=RuntimeConnection.for_inprocess(base_directory=str(out_folder / "sessions")),
        github={"use_logged_in_user": False},
    )
    await client.start()
    try:
        for name in names:
            result = await run_variant(client, settings, base_url, key, all_variants[name])
            result = {
                "variant": name,
                "target": target,
                "model_from_configuration": settings.model_name,
                "prompt": PROMPT,
                **result,
                "requests": take_requests(),
            }
            text = json.dumps(result, indent=1, default=str, ensure_ascii=False)
            for secret in (key, real_key):
                if secret:
                    text = text.replace(secret, "[key removed]")
            (out_folder / f"{target}-{name}.json").write_text(text)
            print(f"{name}: done in {result.get('seconds_total', '-')} s", flush=True)
    finally:
        await client.stop()


asyncio.run(main())
```

```bash
#!/usr/bin/env bash
# Starts the backend and the page of the product for the trial. Throwaway.
#   start_product.sh <run folder> <backend port> <page port> [made-up-key]
# The backend gets the model key from the environment of the session, or a
# made-up key when the fourth argument is given. Nothing here prints a key.
set -euo pipefail
RUN=$1; BACKEND_PORT=$2; PAGE_PORT=$3; MODE=${4:-real-key}
REPO=/home/user/AI-Articheture-Research
mkdir -p "$RUN"
export POC_DATABASE_FILE="$RUN/app.db" POC_SESSION_DIRECTORY="$RUN/sessions"
POC_TOKEN_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
export POC_TOKEN_SECRET_KEY
if [ "$MODE" = "made-up-key" ]; then
  POC_MODEL_API_KEY="made-up-$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
  export POC_MODEL_API_KEY
fi
cd "$REPO/backend"
# A throwaway user with a password made now. The file stays in the scratch folder.
python3 -c 'import secrets; print(secrets.token_urlsafe(16), end="")' > "$RUN/password.txt"
{ cat "$RUN/password.txt"; echo; cat "$RUN/password.txt"; echo; } \
  | uv run --no-sync python -m app.create_user trial_user > "$RUN/create_user.log" 2>&1
setsid nohup uv run --no-sync uvicorn app.main:app --port "$BACKEND_PORT" > "$RUN/backend.log" 2>&1 &
echo $! > "$RUN/backend.pid"
cd "$REPO/frontend"
POC_BACKEND_ADDRESS="http://127.0.0.1:$BACKEND_PORT" setsid nohup npx vite --port "$PAGE_PORT" --strictPort \
  > "$RUN/frontend.log" 2>&1 &
echo $! > "$RUN/frontend.pid"
for _ in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:$BACKEND_PORT/health" > /dev/null \
     && curl -sf "http://127.0.0.1:$PAGE_PORT/" > /dev/null; then
    echo "backend and page are up"; exit 0
  fi
  sleep 0.5
done
echo "not up in time"; exit 1
```

```bash
#!/usr/bin/env bash
# Stops what start_product.sh started. Each server leads a process group.
RUN=$1
for name in backend frontend; do
  if [ -f "$RUN/$name.pid" ]; then
    kill -TERM -- "-$(cat "$RUN/$name.pid")" 2>/dev/null || kill -TERM "$(cat "$RUN/$name.pid")" 2>/dev/null || true
  fi
done
sleep 2
rm -f "$RUN/password.txt"
echo stopped
```

```javascript
// Drives the page of the product in a real browser. Throwaway. Not project code.
//   node browser_run.js <output folder> <page address> <password file> <plan>
// plan "main": two conversations with the real model. plan "made-up-key": one message.
const { chromium } = require('playwright');
const fs = require('fs');

const [OUT, BASE, PASSWORD_FILE, PLAN] = process.argv.slice(2);
const ANSWERS = 'article[aria-label="Answer"]';
const results = { plan: PLAN, turns: [], console: [] };

async function watch(page) {
  // Notes the time of every change of the page, with the state of the answer.
  await page.evaluate((answers) => {
    window.__marks = [];
    if (window.__observer) window.__observer.disconnect();
    window.__observer = new MutationObserver(() => {
      const all = document.querySelectorAll(answers);
      const last = all[all.length - 1];
      const working = Array.from(document.querySelectorAll('[role="status"]'))
        .some((e) => e.textContent.includes('The model is working'));
      window.__marks.push([performance.now(), all.length, last ? last.textContent.length : 0, working]);
    });
    window.__observer.observe(document.body, { subtree: true, childList: true, characterData: true });
  }, ANSWERS);
}

async function lines(page) {
  return page.evaluate(() => Array.from(document.querySelectorAll('[role="alert"], [role="status"]'))
    .map((e) => e.getAttribute('role') + ': ' + e.textContent.trim()));
}

async function send(page, name, text, options = {}) {
  await page.getByRole('textbox', { name: 'Message' }).fill(text);
  const before = await page.locator(ANSWERS).count();
  await watch(page);
  const start = await page.evaluate(() => performance.now());
  await page.getByRole('button', { name: 'Send' }).click();
  if (options.stopAfterMs !== undefined || options.shotAfterMs !== undefined) {
    await page.waitForFunction(([s, n]) => document.querySelectorAll(s).length > n, [ANSWERS, before], { timeout: 120000 });
    await page.waitForTimeout(options.stopAfterMs ?? options.shotAfterMs);
    await page.screenshot({ path: `${OUT}/${name}-while-arriving.png` });
    if (options.stopAfterMs !== undefined) await page.getByRole('button', { name: 'Stop' }).click();
  }
  await page.getByRole('button', { name: 'Send' }).waitFor({ timeout: 180000 });
  const end = await page.evaluate(() => performance.now());
  await page.waitForTimeout(600);
  const marks = await page.evaluate(() => window.__marks);
  const seconds = (t) => (t === undefined ? null : Math.round(t - start) / 1000);
  const working = marks.find((m) => m[3]);
  const arriving = marks.filter((m) => m[1] > before && m[2] > 0);
  const lengths = [...new Set(arriving.map((m) => m[2]))];
  const lastGrowth = arriving.filter((m) => m[2] === Math.max(...lengths))[0];
  const box = await page.evaluate(() => {
    const b = document.querySelector('.chat-messages');
    return b ? Math.round(b.scrollHeight - b.scrollTop - b.clientHeight) : null;
  });
  const count = await page.locator(ANSWERS).count();
  const turn = {
    name,
    text,
    seconds_until_working_line: seconds(working && working[0]),
    seconds_until_first_piece: seconds(arriving[0] && arriving[0][0]),
    seconds_until_last_piece: seconds(lastGrowth && lastGrowth[0]),
    seconds_until_send_button_is_back: seconds(end),
    times_the_answer_grew_on_the_page: lengths.length,
    longest_answer_characters_seen: lengths.length ? Math.max(...lengths) : 0,
    answers_on_the_page_before: before,
    answers_on_the_page_after: count,
    last_answer_after: count > 0 ? (await page.locator(ANSWERS).last().innerText()).slice(0, 4000) : null,
    pixels_from_the_bottom_of_the_chat: box,
    lines_on_the_page: await lines(page),
  };
  results.turns.push(turn);
  fs.writeFileSync(`${OUT}/results.json`, JSON.stringify(results, null, 1));
  await page.screenshot({ path: `${OUT}/${name}.png` });
  console.log(`${name}: first piece ${turn.seconds_until_first_piece} s, end ${turn.seconds_until_send_button_is_back} s, `
    + `grew ${turn.times_the_answer_grew_on_the_page} times, ${turn.longest_answer_characters_seen} characters`);
  return turn;
}

async function newConversation(page) {
  await page.getByRole('button', { name: 'New conversation' }).click();
  await page.waitForURL(/#\/conversations\/[0-9a-f]{32}$/);
  // The chat of the conversation before must be gone, and the new one loaded.
  // Text that is filled in earlier is lost when the chat changes.
  await page.waitForFunction(() => document.querySelectorAll('article').length === 0
    && document.querySelector('textarea[aria-label="Message"]')
    && !document.querySelector('textarea[aria-label="Message"]').readOnly);
  await page.waitForTimeout(500);
  return page.url().split('/').pop();
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 2,
    recordVideo: { dir: `${OUT}/video`, size: { width: 1280, height: 800 } },
  });
  const page = await context.newPage();
  page.on('console', (m) => { if (m.type() === 'error') results.console.push(m.text().slice(0, 300)); });
  page.on('pageerror', (e) => results.console.push('pageerror: ' + String(e).slice(0, 300)));

  await page.goto(BASE);
  await page.getByLabel('User name').fill('trial_user');
  await page.getByLabel('Password').fill(fs.readFileSync(PASSWORD_FILE, 'utf8'));
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByText('Signed in as trial_user').waitFor();

  if (PLAN === 'made-up-key') {
    results.conversation = await newConversation(page);
    await send(page, 'made-up-key', 'Hello. Please answer with one word.');
  } else {
    results.first_conversation = await newConversation(page);
    await send(page, '1-question', 'What is the capital of Australia? Answer in one sentence.');
    await send(page, '2-follow-up', 'Roughly how many people live in that city? One sentence.');
    await send(page, '3-long-answer',
      'Write a short guide to making a cup of tea. Use a heading, a numbered list of steps, '
      + 'a short code block that shows the steps as Python pseudocode, and a small table '
      + 'that compares green tea and black tea.', { shotAfterMs: 1500 });
    // The same answer from its top, to see the heading, the list and the code block.
    await page.locator('article[aria-label="Your message"]').last().scrollIntoViewIfNeeded();
    await page.evaluate(() => {
      const box = document.querySelector('.chat-messages');
      const mine = document.querySelectorAll('article[aria-label="Your message"]');
      box.scrollTop += mine[mine.length - 1].getBoundingClientRect().top - box.getBoundingClientRect().top;
    });
    await page.waitForTimeout(300);
    await page.screenshot({ path: `${OUT}/3-long-answer-from-its-top.png` });
    await send(page, '4-chinese', '用两三句话解释一下什么是服务器发送事件（Server-Sent Events）。');

    results.second_conversation = await newConversation(page);
    await send(page, '5-stop', 'Write a detailed essay of about 1500 words on the history of the bicycle.',
      { stopAfterMs: 2000 });
    await send(page, '6-after-stop', 'In one sentence: what have I asked you for so far in this conversation?');

    await page.reload();
    await page.getByText('Signed in as trial_user').waitFor();
    await page.locator(ANSWERS).first().waitFor();
    await page.waitForTimeout(500);
    results.after_reload = {
      address: page.url().replace(/^[^#]*/, ''),
      messages_of_the_user: await page.locator('article[aria-label="Your message"]').count(),
      answers: await page.locator(ANSWERS).count(),
      titles_in_the_list: await page.locator('nav[aria-label="Conversations"] a').allInnerTexts(),
    };
    await page.screenshot({ path: `${OUT}/7-after-reload.png` });
    await page.getByRole('button', { name: 'Sign out' }).click();
    await page.getByRole('button', { name: 'Sign in' }).waitFor();
  }
  const video = page.video();
  await context.close();
  if (video) results.video = await video.path();
  await browser.close();
  fs.writeFileSync(`${OUT}/results.json`, JSON.stringify(results, null, 1));
  console.log('console errors of the page:', results.console.length);
})().catch((error) => { console.error('FAILED', error); process.exit(1); });
```
