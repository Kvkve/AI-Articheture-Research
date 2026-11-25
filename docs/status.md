# Current status

Updated 2026-11-25 (US Eastern Time).

## Where the work stands

- The project has three stages so far: setting the rules (done), the technical research (done), and the first PoC (in progress). Use these plain names with the owner. The owner did not agree to short labels for stages and does not want them.
- The first PoC has ten tasks. They are in `docs/tasks.md` under "First PoC", with every design choice and its reason.
- Done so far:
  - Task 1, the skeleton and the automatic checks (pull request #9).
  - The small task before task 2, a check for `docs/architecture.md` (pull request #10).
  - Task 2, the database and the users (pull request #11).
  - Task 3, sign-in (pull request #12).
  - Task 4, the module that touches the SDK (pull request #13).
  - Task 5, the endpoints for conversations (pull request #14).
  - Task 6, chat with streaming (pull request #15).
  - Task 7, the frontend and the browser test (pull request #16).
- What is built, file by file, is in `docs/architecture.md`: one diagram and a table of what each component does. `implementer` updates it as part of each task and `reviewer` checks it against the code. The rule is in `CLAUDE.md`. The file states its own rules near its top.
- What tasks 1 to 3 added, in short:
  - `backend/` is a FastAPI application. Its dependencies are managed with `uv` and locked in `backend/uv.lock`. `frontend/` is a React and TypeScript application made with `create-vite`.
  - `scripts/setup.sh` installs the dependencies. `scripts/check.sh` runs every check. `.github/workflows/checks.yml` runs it on every pull request and on every push to `main`. A Stop hook in `.claude/settings.json` runs it at the end of every turn of the main agent.
  - The check of `docs/architecture.md` reads paths in backticks only. It does not read the diagram. So the table lists every file that the diagram names, and `reviewer` checks that the two agree.
  - The settings, the SQLite file with the tables of users and of conversations, the hash of a password with Argon2, and the script that creates a user.
  - Sign-in. `backend/app/login.py` holds the sign-in endpoint. `backend/app/protected.py` holds the router whose endpoints need a token: every such endpoint goes on this router. `backend/app/dependencies.py` holds what an endpoint can ask for. A token that is missing or not valid always gets status 401.
  - `backend/tests/test_every_endpoint_needs_a_token.py` lists every endpoint of the application. To each one outside a short list of open ones it sends three requests that must be refused. **A pair of method and path is added to that list only when the owner agrees.**
- What task 4 added:
  - `backend/app/agent.py`: the only file that imports the Copilot SDK. A rule of ruff in `backend/pyproject.toml` fails the checks when another Python file in `backend/` or `scripts/` imports it. No type of the SDK leaves the module: it gives out its own small types and raises its own errors.
  - The module has one class, `Agent`. One object serves one backend process. `backend/app/main.py` makes it when the backend starts, starts the runtime of the SDK, and stops it at shut-down. An endpoint asks for it with `AgentDependency` from `backend/app/dependencies.py`.
  - Its three actions, all `async`:
    - `start_conversation()` makes a session on disk and returns its id, 32 random hexadecimal characters.
    - `begin_answer(conversation_id, text)` is step one of sending. It returns an `Answer`. Reading the `Answer` with `async for` is step two and gives the pieces of text. The send endpoint of task 6 uses both steps.
    - `read_history(conversation_id)` returns a list of `HistoryMessage`, each with a role, "user" or "assistant", and a text.
  - Its errors. All are subclasses of `AgentError`: `InvalidConversationIdError`, `UnknownConversationError`, `ConversationBusyError`, `NoModelKeyError`, `ModelProviderError` (it has a `status_code`), and `AnswerTimedOutError`.
  - `backend/app/config.py` has seven settings for it: the model key, the model name, the provider type and address, the folder of the session files, the system prompt, and the longest wait for the next part of an answer.
  - `backend/tests/model_stand_in.py`: a local server that stands in for the model provider in the tests. It speaks the streaming format of the Anthropic Messages API and records the requests it gets.
  - `scripts/setup.sh` also downloads the runtime of the SDK, about 196 MB unpacked, into a cache folder outside the repository.
- What task 5 added:
  - Three endpoints on the router of `backend/app/protected.py`. The owner chose the addresses.
    - POST `/conversations` starts a conversation. It takes no body and answers 201 with the conversation.
    - GET `/conversations` lists the user's own conversations. The answer is an object with the list under the name "conversations".
    - GET `/conversations/{conversation_id}/messages` reads the history. The answer is an object with the list under the name "messages". Each message has a role and a text.
  - A conversation in an answer has four fields: `id`, `title`, `created_at` and `last_active_at`. The title is `null` until the first message of the conversation.
  - `backend/app/conversations.py` holds the SQL of the table of conversations: store a row, list the rows of a user, and find one row by its id and its user in one query.
  - The table of conversations has a new column, `last_active_at`: the time of the last activity. The list is ordered by it, the latest first. The owner chose this order. Of two conversations with the same time, the one made later comes first. Both times of a conversation are stored in UTC with milliseconds. Since task 6, every accepted message sets the time of the last activity.
  - Ownership. The history endpoint looks for the row with the id and the signed-in user before it calls the agent. When there is none, it answers 404 with the text "Conversation not found". The answer is the same for a conversation of another user, for an id that no conversation has, and for an id of another form.
  - `backend/app/agent_errors.py` is the one place that gives an error of the agent module its status code. The endpoints let the error rise. `ConversationBusyError` gets 409. Since task 6, `NoModelKeyError` gets 503. Every other `AgentError` gets 500. The answer is JSON with a fixed text, and the text of the error goes to the log only.
  - Starting a conversation has two steps: the agent makes the session, then the endpoint stores the row. When the row cannot be stored, the session stays on disk, the log names its id, and the answer is 500. The owner chose this.
  - The endpoints that call the agent are `async def` and run on the event loop. Their database calls block the loop for a moment, which is accepted. The list does not call the agent and is a plain `def`.
- What task 6 added:
  - One endpoint on the router of `backend/app/protected.py`: POST `/conversations/{conversation_id}/messages`. The body is JSON with one field, `text`. The answer is a stream of Server-Sent Events.
  - The steps of a request, in order. Each refusal is an ordinary JSON answer with a status code, never a stream.
    1. The token: 401.
    2. The body: 422 for no text, an empty text, only white space, or a text longer than the setting. Every 422 has the shape that FastAPI gives a body that fails validation. The answer for a text that is too long gives the limit as the number `max_length` under `ctx`. This check comes before the next one.
    3. Ownership: the same 404 as the history, and the agent is not called.
    4. Step one of the agent module: 409 for a conversation that is still answering, 503 with no model key, 500 otherwise.
    5. One write to the table of conversations: the time of the last activity becomes now, and a row with no title gets one.
    6. The stream starts, with status 200.
  - The stream. Each message is one line that begins with "data:" and holds a JSON object. The field `type` is "text", "end" or "error". A "text" message has the field `text`, one piece of the answer. An "error" message has the field `message`, one fixed, general text. A stream ends with exactly one "end" or one "error". A stream that closes with neither was cut off. A line that begins with a colon is a comment that FastAPI sends when the stream is quiet for 15 seconds. A reader skips it. The "event:" line is not used.
  - When the agent module fails while the answer streams, the stream ends with the "error" message. The cause goes to the log of the backend, with the status code of the provider.
  - The title: every run of white space in the first message becomes one space, the ends are trimmed, and the first characters are kept. Nothing marks a cut.
  - Two settings in `backend/app/config.py`. `POC_LONGEST_MESSAGE_CHARACTERS` is the longest message, 20,000 by default. `POC_TITLE_CHARACTERS` is how many characters a title keeps, 50 by default. A character is one Unicode code point.
  - How the code is built. The steps that can refuse a message are in a dependency, `begin_sending`, because a dependency runs before the status 200 goes out. The code of a path function that uses `yield` runs only after it. The same dependency closes the answer after the stream has ended, also when the reader has gone away. The path function, `send_message`, reads the answer and yields one model for each message.
  - The contract is in the generated API documentation: the request, the three kinds of message with a description each, and the answers 404, 409, 422, 500 and 503. A test reads `/openapi.json` and checks this.
  - `backend/app/agent_errors.py` also holds the text of the 503 and the text of the "error" message of a stream.
  - `backend/app/conversations.py` has two new functions: `make_title` and `record_message`.
  - `backend/tests/test_send_message.py` holds the 25 tests of the endpoint.
  - No table changed. A database file from task 5 still works.
- What task 7 added:
  - The web interface, in `frontend/src/`. `docs/architecture.md` names each file and what it does. The backend did not change.
  - The page calls its own address, on paths that begin with `/api`. The development server of Vite passes these calls on to the backend with the prefix taken off. The rule is in `frontend/vite.config.ts`. The address of the backend is the variable `POC_BACKEND_ADDRESS`, by default `http://127.0.0.1:8000`. This is for development only.
  - `frontend/src/backend.ts` is the only file that calls `fetch`. A rule in `frontend/eslint.config.js` fails the checks when another file of `frontend/src/` does. The module turns each answer into its own types and errors: `SignInAgainError` for a 401, `BackendError` with a text for the user, `UnreachableError`, and `AnswerStoppedError`.
  - `frontend/src/answerStream.ts` reads the stream of an answer from byte chunks. It skips a kind of message that it does not know. Task 9 relies on this.
  - The token is in `sessionStorage`, and only `frontend/src/tokenStore.ts` touches it. A conversation has the address `#/conversations/<conversation id>`, and only `frontend/src/address.ts` reads and writes it.
  - What the chat does at each ending of a stream. "end": the answer stays. "error": a line shows its text. A stream that was cut: a line says that the connection was lost. "Stop": the page closes the connection, and a line says that the answer was stopped. A stream that breaks its format: a line says that the page cannot read the answer. After every ending but "end" the page reads the history again and shows what it holds. Leaving a conversation, signing out and a reload close the connection too.
  - The names on the page that a test can use: the fields "User name" and "Password" and the button "Sign in"; the text "Signed in as" with the name, and the button "Sign out"; the navigation "Conversations", with a link for each conversation and the button "New conversation"; the text box "Message" with the buttons "Send" and "Stop"; a message of the user is an article named "Your message", and an answer is an article named "Answer". Ask for the text box by its role: a search by label for "Message" also finds "Your message".
  - The frontend has 50 unit tests in three files next to the code: `App.test.tsx`, `backend.test.ts` and `answerStream.test.ts`.
  - The browser test, `backend/tests/test_browser.py`. It starts the stand-in, the backend under uvicorn, the development server and a headless Chromium, and drives the page as two users. It is marked "browser". The plain pytest leaves it out, and the last step of `./scripts/check.sh` runs it alone.
  - `backend/pyproject.toml` pins `playwright==1.63.0`. `scripts/setup.sh` installs the browser for it, unless the machine says that it brings its own. The checks on GitHub install the system libraries of the browser, and passed with the browser test at the first try.
- The title of a conversation (the owner's choice on 2026-11-24): the table of conversations has a `title` column. The title is the opening of the first message. Task 6 writes it. The list of conversations gives it, and gives `null` while there is none. The frontend shows "New conversation" for `null`.
- The choices of the first PoC in one line each. The reasons and the accepted costs are in `docs/tasks.md`.
  - Agent layer: the Copilot SDK. It was not compared with other options. All code that touches it stays in one module.
  - The runtime runs inside the backend's own process.
  - The conversation history lives only in the SDK's session files. The application keeps its own table of which user owns which conversation, with a short title and the time of the last activity.
  - Answers travel to the browser by Server-Sent Events, in the project's own small message format.
  - The frontend is hand-written React components. The code that talks to the backend is one module.
  - Sign-in is a user name and a password with a signed token, kept to the least. It follows the official FastAPI template and stands in for single sign-on.
  - The open endpoints are sign-in, `/health` and the pages of the generated API documentation. Every other endpoint needs a token.
  - The secret key that signs the tokens is random at each start of the backend, unless the variable `POC_TOKEN_SECRET_KEY` gives one. A restart signs every user out. This fits one backend process only.
  - The database is SQLite, with SQL written by hand.
  - The default model is Claude Haiku 5.5, set in configuration.
  - The interface shows the model's reasoning. This is the last building task and is dropped if it proves troublesome.
  - The runtime of the SDK is under the "GitHub Copilot CLI License", which is not an open-source license. The owner chose on 2026-11-24 to go on using it: the project only downloads and runs it. `docs/sources.md` records it.
  - The settings class reads the model key from the variable `POC_MODEL_API_KEY`. With no key the backend starts, and a message is refused.
  - When the reader of an answer goes away before the end, the module stops the model. A reload cuts off an answer that is being written.
  - For every message the module resumes the session from disk, gets the answer and disconnects. No session stays open in memory between messages.
  - The module keeps in memory which conversations are answering. This fits one backend process only.
  - The addresses of conversations: one address for the conversations and one for the messages of a conversation. Reading is GET, and sending is POST on the address of the messages.
  - The list of conversations is ordered by the last activity.
  - A session whose row could not be stored stays on disk.
  - An error of the agent module gets 409 when the conversation is still answering, 503 when the backend has no model key, and 500 otherwise.
  - In the stream of an answer, the kind of a message is the field `type` of a JSON object. The "event:" line of Server-Sent Events is not used.
  - The longest message is a setting, 20,000 characters by default. The number is the main agent's estimate.
  - The page reaches the backend through the development server of the frontend, which passes the calls on. The backend allows no other address.
  - The browser keeps the token in the storage of the tab. A reload keeps the sign-in, and a closed tab ends it.
  - A conversation has its own address in the browser, after the hash. The project wrote this itself, with no router library.
  - The browser test is Python, with pytest and Playwright, and is the last step of the check command.
  - The page is plain CSS written by hand. Leaving a conversation that is answering stops the answer.
  - No decision record is written. The choices are cheap to change in a first PoC. The next number is 0007.
- What the owner wants from the project, said on 2026-11-23:
  - Do not make the start complicated.
  - The final platform may serve hundreds of users at once. Three choices of the first PoC do not carry over to that size: where the runtime runs, where the history lives, and the database. `docs/tasks.md` lists this under "Later". The random secret key and the busy marks in memory do not carry over either: both fit one backend process only.
  - Each team may later have its own frontend. So the backend API and the message format are a contract: written down, and free of anything only one frontend needs.
  - People the owner works with also recommend the Copilot SDK. The owner cannot share their documents. Do not ask for them.
- What the research, the trials and task 4 found about the SDK, in short. The full account is in `docs/research/reports/第一版 PoC 技术调研.md`, in the trial note next to it, and under task 4 in `docs/tasks.md`.
  - With no GitHub sign-in, the SDK started, streamed an answer, stored the conversation on disk, resumed it and read the history back. This held against a local stand-in and against a real model (one run).
  - The runtime adds its own system prompt. `system_message` with mode "replace" swaps it for the application's own text.
  - With a real model the runtime chooses several request settings by itself: thinking on, effort "medium", an output limit of 48,000 tokens, and prompt-cache markers. Whether the application can change them is not tested. The session options of the SDK have fields named `reasoning_effort` and `reasoning_summary`. Task 8 can try them.
  - `mode="empty"`, which the vendor advises for shared use, demands an explicit storage directory and an explicit tool list for each session.
  - The SDK has no notion of a user and no lock. The module lets one action at a time into a conversation.
  - The SDK can stop an answer that is being written, with `abort`. The history then holds the user's message and no part of the stopped answer.
  - A resume takes about 0.03 seconds and a disconnect about 0.005 seconds, against the stand-in with short conversations.
  - Every stop of the runtime takes one second inside the SDK.
  - A stopped client of the SDK starts a new runtime by itself when it is called. The module checks before every call that it still holds the client.
  - The runtime tries a failed request again by itself for some errors: status 500 six times over about 17 seconds.
  - The runtime runs `git` commands in the working directory of the backend and stores that directory in the session files. No request to the provider held any of this.
  - Under BYOK the SDK reports a cost of 0. The application must work out cost from the token counts.
  - The SDK changes fast. It is pinned at exactly 2.0.1, the version of the trial runs. Version 2.0.2 came out on 2026-11-24.
  - The SDK can delete a session, with `delete_session` of its client. Seen in its source on 2026-11-24 and not tried. The agent module has no action for it.
  - The session files of a conversation are in a folder named by the conversation id, inside a folder named session-state in the folder of the session files. One test of task 5 reads this layout.
- Model key: the project environment `AI-Articheture-Research` holds a Claude API key as the variable `POC_MODEL_API_KEY`. The settings class reads it. So a backend that is started by hand in a session on that environment has the real key and the real provider address. **A message sent to such a backend calls the real model and costs money.** For a trial by hand that needs no model, start the backend with the variable removed, for example with `env -u POC_MODEL_API_KEY` in front of the command. It then answers a message with 503. To see answers with no real model, point it at the stand-in: see "How to run and verify". The tests are safe: `backend/tests/conftest.py` removes the key and the other model variables before every test. Only task 8 means to call the real model. The browser test is safe too: it gives the backend the environment of the test, and checks that the stand-in got the key of the test.
- Cloud environments: the project environment allows `github.com`, `release-assets.githubusercontent.com`, `api.anthropic.com` and the package registries. It has one variable and a setup script. The script calls `scripts/setup.sh` when a new machine is built for a session.
  - Seen on 2026-11-24, in the sessions for task 3 and for task 4: the session started with the packages from before the last tasks. The checks failed at the mypy step with "Cannot find implementation or library stub". `./scripts/setup.sh` fixed it. Run it at the start of a session when a check fails this way. The sessions for task 5 and for task 6 started with the right packages. The session for task 7 on 2026-11-25 failed this way again.
  - A cloud session has a Chromium installed for exactly Playwright 1.63.0, in the folder that the variable `PLAYWRIGHT_BROWSERS_PATH` names, and it sets `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD`. The environment does not allow the hosts that Playwright downloads a browser from. This is why `backend/pyproject.toml` pins `playwright==1.63.0`. If the browser test one day cannot find its browser in a new session, the image of the session has moved to another version: `npm ls -g playwright` shows it. Change the pin and `backend/uv.lock` to that version.

## How the work with the owner goes

These points come from the owner. The rules themselves are in `AGENTS.md` and `CLAUDE.md`.

- Teaching: no prediction questions, explain-back questions or practice exercises. The owner learns through real work. The focus is the overall design and the key decisions.
- For a choice, give the options, the cost of each and a recommendation, and ask whether the owner agrees. Do not ask the owner to justify a choice the research gave no material for. Say plainly where the research did not compare options.
- Explain a new idea from what the owner knows: SQL, some Java and Python. The owner has used SQLite.
- Merging: a pull request is merged only when the owner agrees. The owner may tell the main agent in the conversation to merge it. The main agent first says in Chinese what the pull request changes.
- Collect small record changes into one pull request. Do not open a pull request for each.
- Trial runs call a low-cost model, not Opus. Review subagents stay on the model in their definition.
- No company content. The owner's workplace has internal documents on this topic. They must not be uploaded or copied into the repository.
- Dates in files are US Eastern Time. The clock of a cloud session shows UTC, which is a day ahead in the evening. Check with `TZ=America/New_York date`.
- How the owner learns, said on 2026-11-24. The owner studies general ideas elsewhere, in another session or with another tool: HTTP, APIs, tokens, streaming. The building goes on here. After each task the owner asks about it in broad terms: the summary in Chinese and what changed in the diagram of `docs/architecture.md`. The owner does not read code line by line. Configuration files and scripts are black boxes unless the owner asks.
- The owner watches the usage of the main model, and asked about it on 2026-11-24. The main agent's reading of this, not the owner's words: keep each session to one task, and put long explanations in a separate session.
- The owner means to get hands-on when building in the work setting. The main agent suggested that the owner runs the trial of task 8 in the browser in person. The owner has not said yes or no to that. Whether the owner writes any part by hand is the owner's choice. Do not set exercises.
- A choice can be asked with the question form of the session, with the recommended option first. Each question must stand by itself, because the owner may see only the form. The owner answered the choices of tasks 3, 4, 5 and 6 this way. In task 5 the owner took another option than the recommended one for the order of the list. So the owner reads the options, and the costs must be written with care. In task 6 the main agent first wrote the options and the small choices it would make by itself in the conversation, in Chinese, and then asked with the form. In task 7 it did the same, with a table of the options and their costs for each choice, and the owner took the four recommended options.

## Next step

1. Task 8 of the plan: the trial with the real model. Start a new session for it, on the project environment `AI-Articheture-Research`. It is the only task that calls the real model.
2. Then tasks 9 and 10 of the plan, one at a time.

For task 8. Before the work, ask the owner how the trial runs. The main agent's guess at the options, not checked:

- The main agent runs the page in the cloud session against the backend with the real key, drives it with Playwright, and shows screenshots. The owner does not touch the page.
- The owner runs the page in person. The page of a cloud session is on the machine of that session. Whether the owner can open it from outside was not tried. On the owner's own computer it needs the repository, `uv`, `npm` and a model key there.
- The main agent suggested "in person" on 2026-11-24. The owner has not said yes or no.

What is ready for task 8, and what is not known:

- The plan of task 8 in `docs/tasks.md`, with its acceptance criteria.
- A backend started by hand in a session on the project environment has the real key. "How to run and verify" says how to start the backend and the page together.
- The default model is Claude Haiku 5.5, set in configuration. No run has used it yet. The one real run so far used another model.
- The page has only been seen with the stand-in. Not seen with a real model: how fast the pieces come, a long answer with scrolling, and the Markdown that a model really writes. A table in an answer shows as plain text with bars, because the page has no add-on for tables.
- The findings go into the trial note, `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`: the request settings that the runtime chooses for this model, the timing and the token counts. The task also finds out whether the application can change the thinking, effort and output limit settings. The session options of the SDK have fields named `reasoning_effort` and `reasoning_summary`.
- Never print the key, and keep it out of every file.

How to start a session on the project environment: on the screen for starting a new session, the environment selector is the first control in the row under the message box. It is shown only until the first message is sent.

## How to run and verify

- Install the dependencies: `./scripts/setup.sh`. It needs `uv` and `npm`. It installs from the lock files only. Then it downloads the runtime of the SDK from `github.com`, if the cache does not hold it yet.
- Run every check: `./scripts/check.sh`. It takes about 150 seconds, of which the tests of the backend take about 130: about 95 tests stop the runtime of the SDK, and each stop takes one second inside the SDK. Every later test that starts the backend adds one second. The tests of the frontend take about 2 seconds, and the browser test, the last step, about 6. It stops at the first failure and names the failed step. The last line of a good run is "All checks passed."
  - Run ruff and mypy through this command. A `ruff check` typed by hand from `backend/` with other paths reads the rules another way and reports errors that are not there.
- Start the backend: `cd backend && uv run uvicorn app.main:app --reload`. Then open `http://127.0.0.1:8000/health` or the generated API documentation at `http://127.0.0.1:8000/docs`. The first start makes the database file and its tables, and the folder of the session files.
- Create a user: `cd backend && uv run python -m app.create_user <user name>`. The script asks for the password twice. It also makes the database file and the tables if they are missing.
  - In a session with no terminal, give the password on standard input, on two lines. Python warns that it cannot hide the input, and the script still works. Use this only for a throwaway user in a trial, with a password made at run time.
- Sign in by hand: on the page `/docs`, press "Authorize" and give the user name and the password. The page then sends the token with every request, and every endpoint can be tried there. From a command line, send the form fields `username` and `password` to `POST /login/access-token`, and send the token in the header `Authorization: Bearer <token>`.
- Try the conversations by hand, signed in: POST `/conversations` gives a new conversation with its id. GET `/conversations` gives the list. GET `/conversations/<id>/messages` gives the history.
- Send a message by hand: `curl -N -X POST http://127.0.0.1:8000/conversations/<id>/messages -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"text": "Hello"}'`. The option `-N` shows each message of the stream as it arrives. **With the real key in the environment this calls the real model and costs money.** Whether the page `/docs` shows a stream as it arrives was not tried.
- Run the backend against the stand-in by hand, with no real model. This worked on 2026-11-24, in a small Python script in a scratch folder, run with `uv run python` from `backend/`.
  - The script puts `backend/tests` on its import path and starts the stand-in with `running_stand_in()` of `backend/tests/model_stand_in.py`. It tells the stand-in how to answer with `answer(...)`, `answer_and_hold(...)` or `fail(400)`.
  - It starts uvicorn as a child process. The environment of the child has no variable that begins with `POC_` and no proxy variable of the machine. It has `NO_PROXY=127.0.0.1`, `POC_MODEL_PROVIDER_ADDRESS` with the address of the stand-in, a made-up `POC_MODEL_API_KEY`, and scratch paths in `POC_DATABASE_FILE` and `POC_SESSION_DIRECTORY`.
  - It calls the backend with `httpx` and `trust_env=False`, so that the calls do not go through the proxy of the machine.
  - On 2026-11-25 a helper of this kind also made two users and planned each answer to send two pieces, hold for three seconds, and send the rest. A person then sees an answer arrive in pieces and has time to press "Stop". Such a helper must stop its backend when it is killed: the first version left one running.
- The secret key: with no variable, every start of the backend makes a new key, and the tokens from before are refused. With `--reload`, every saved change to the backend code is a restart. To keep the tokens, set `POC_TOKEN_SECRET_KEY` to a random text of at least 32 characters. Never write a key into a file of the repository.
- Where the data is. By default both places are in the folder `data` inside `backend/`. Git ignores that folder.
  - The database file is `app.db`. The variable `POC_DATABASE_FILE` names another file.
  - The session files of the SDK are in the folder `sessions`, one folder for each conversation, as plain text. The variable `POC_SESSION_DIRECTORY` names another folder.
  - Give absolute paths: a relative one is read from the folder where the command is started.
  - The two belong together. A row of the table of conversations names a session folder. Delete or move both, not one. A row whose session folder is gone makes the history answer 500.
  - **A database file from before task 5 lacks the column `last_active_at`.** The list then fails. The project has no tool that changes a table. Delete the folder `data` and start again. This holds for every later change to a table too.
- The model settings: `POC_MODEL_API_KEY`, `POC_MODEL_NAME`, `POC_MODEL_PROVIDER_TYPE`, `POC_MODEL_PROVIDER_ADDRESS`, `POC_SYSTEM_PROMPT` and `POC_ANSWER_WAIT_SECONDS`. The settings of sending: `POC_LONGEST_MESSAGE_CHARACTERS` and `POC_TITLE_CHARACTERS`. The defaults are in `backend/app/config.py`.
- To look inside the database in a cloud session, use Python's `sqlite3` module. The `sqlite3` command-line tool is not installed there.
- A line that the backend's own code writes to the log shows in the output of uvicorn with no level in front, for a warning or an error. Lines of a lower level are not shown.
- Start the page: `cd frontend && npm run dev`. The command prints the address to open. The page needs a backend that runs: by default the development server passes the calls on to `http://127.0.0.1:8000`, where the command above starts the backend. The variable `POC_BACKEND_ADDRESS` names another address.
- Use the page: create a user with the script, open the address, and sign in. **With the real key in the environment, each message calls the real model and costs money.**
- Run the tests of the frontend alone: `cd frontend && npm run test`. Run the browser test alone: `cd backend && uv run --no-sync pytest -m browser`.
- Drive the page by hand in a cloud session with the Playwright that the session has installed: in a Node script, `require('playwright')` works from any folder, and `chromium.launch()` needs no options. Keep the script and its screenshots in a scratch folder. On 2026-11-25 the main agent tried the page this way, against a backend with the stand-in.
- Where the rules of the checks are: `backend/pyproject.toml` for Python, `frontend/eslint.config.js` and the `tsconfig` files for TypeScript.
- A new Python file in `scripts/` must be added to the list `known-first-party` in `backend/pyproject.toml`. Without this, the import-order rule sorts its imports wrongly.
- Run pytest from `backend/` with no path argument, or with `-k`. A path argument outside `backend/` skips the settings, and the tests in `scripts/tests/` then cannot import their modules.
- Backend tests:
  - `backend/tests/conftest.py` gives every test its own database file and its own session folder in a temporary folder, and its own settings. No test may write to the default places. It removes the token variables and the model variables of the machine before every test.
  - The same file has the helpers. `client` starts the application. `add_user` stores a user with a password made at run time. `sign_in` returns a token for that user. `stand_in`, `stand_in_address` and `model_key` start the stand-in for the model provider and point the settings at it. `portal_of` gives the portal of the test client. `bearer` makes the header with the token. `start_conversation` starts a conversation through its endpoint. `run_sql` runs one statement on the database file. `the_agent` gives the agent object of the application. `wait_until_free` waits until a conversation is no longer busy.
  - A new setting needs its variable in the list of the fixture `fresh_settings`, so that a variable of the machine cannot change a test result.
  - A test that needs another value of a setting sets the variable in a fixture and names that fixture with `usefixtures`, in front of the fixtures that start the application. The application reads the settings when it starts. See `small_limits` in `backend/tests/test_send_message.py`.
  - The test client streams for real. With `client.stream(...)` a test reads a message while the application still writes the next. When the test leaves the `with` block early, the application sees a reader that has gone away. Starting the application starts the runtime of the SDK, and stopping it costs one second.
  - A test makes its passwords and keys at run time, for example with `secrets.token_urlsafe`. Do not write a fixed password or key in the code, and do not add an exception to the linter's rule against it. That rule also flags a fixed text that is given to, or compared with, a name that has the word "token" in it, such as the token type "bearer". The code avoids this without an exception: see the model `Token` in `backend/app/login.py`.
  - The tests of the agent run the real SDK and runtime against the stand-in. The runtime follows the proxy variables of the machine, so the fixture `stand_in_address` removes them. A test steers the stand-in with events and not with waits of a fixed length.
  - A test may not import the SDK. To see whether a session of the SDK is still open, one test reads private state of the SDK's client through the agent object, and says so in a comment.
  - pytest has no plugin for `async def` tests here. A test of the agent is a plain function that runs its steps with `asyncio.run()`. A test that starts the application calls the agent through the portal of the test client.
  - A test of an endpoint reaches the one agent object of the application as `app.state.agent`. It can replace an action on that object with `monkeypatch.setattr`, to record calls or to raise an error.
  - The tests of task 5 send a message through the agent object, and write a title or a time into the table with SQL, so that each tests its own endpoint alone. The tests of task 6 send through the endpoint.
  - The browser test starts the backend and the development server as child processes on free ports, each in a process group of its own, and stops them at the end. The fixtures of `backend/tests/conftest.py` set the environment of the test process, and the backend gets that environment. When the test fails, pytest shows the text of the page, the console of the browser and what both servers wrote.
- Frontend tests:
  - They run in Vitest with a made-up page (jsdom). No request leaves a test: a test replaces `fetch` with `vi.stubGlobal`.
  - The rule that only `frontend/src/backend.ts` calls `fetch` holds for the test files too.
  - The tests of the stream reader feed it byte chunks that the test cuts where it wants.
  - How to show that a test of the frontend catches a fault: copy the file to a scratch folder, change the file, run `npx vitest run` in `frontend/`, and put the copy back. For the browser test, change the file of the page or of the backend and put it back with `git checkout`, or work in a scratch copy of the two folders. This worked on 2026-11-25.
- How to show that a test catches a fault, with no change to a file of the repository. This worked on 2026-11-24. Write a small Python file in a scratch folder that imports the application and adds the faulty part in memory. Run pytest from `backend/` with that folder and `.` in `PYTHONPATH`, and name the file with the option `-p`.
  - `backend/app/protected.py` imports the functions of `backend/app/conversations.py` by name, and the text of the stream's error message too. So the faulty part must replace the name in the module of the endpoints, not in the module it comes from.
- In `docs/architecture.md`, put only paths that exist in the repository, and addresses of the API that begin with `/`, in backticks. Any other text in backticks fails the check. This includes the path of the database file, which is made at run time, the names of environment variables, and a method in front of an address. Every file that the diagram names must also be in the table.
- How to draw the diagram of `docs/architecture.md` in a cloud session. This worked on 2026-11-24. Install the `mermaid` package with `npm` into a scratch folder outside the repository. Open a blank page in the browser that comes with the session's Playwright. Load the file `dist/mermaid.min.js` of the package into the page. Call `mermaid.render` with the text of the diagram and take a screenshot. The version was Mermaid 12.3.0. GitHub may draw with another version, so the picture on GitHub is the one that counts. On 2026-11-25 the session refused the install of the package, for `implementer` and for the main agent. The diagram was then checked by reading its text: every box that an arrow names is there, every group is closed, and every file in a box is in the table. Do not work around such a refusal.
- A cloud session has a hook of its own that asks for a commit and a push when a turn ends with changes that are not committed or not pushed. Push the work branch before ending a turn.
- The Stop hook of the project runs in a cloud session too.
- Subagents:
  - A subagent starts in the background even when the call asks for the foreground. On 2026-11-24 every one did. The turn of the main agent then ends while the subagent still writes. The session's hook asks for a commit, and the Stop hook may report failed checks. Do neither. Wait for the subagent's report, check the work, then commit.
  - Write each brief to a file in the scratch folder and give the subagent the path. `reviewer` then reads the same brief that `implementer` worked from. Add each round of changes to the end of that file.
  - For a round of fixes, or a second review round, send a message to the same subagent. It keeps what it has read. This worked on 2026-11-24, in tasks 4, 5 and 6. The tool that sends the message may have to be loaded first.
  - Before the brief, the main agent can try an unsure point of a library in a small script in the scratch folder, and name the script in the brief. In task 6 two such scripts showed how the Server-Sent Events of FastAPI behave, and `implementer` built on them with no stop.
  - A limit in a brief that is not in the acceptance criteria of `docs/tasks.md` can stop `implementer`. On 2026-11-24 a time limit for the checks did. Say in the brief which points come from `docs/tasks.md` and which the main agent added. The brief of task 5 did, and `implementer` did not stop.
  - Ask `implementer` to report, for the main tests, whether it saw each one fail when the thing it guards was broken. The main agent then tries a few of these itself.
  - A task in two parts: the main agent accepted and committed the first part, added the second part to the end of the brief file, and sent the same `implementer` a message. It kept what it had read. This worked on 2026-11-25.
  - A draft pull request, opened before the review has ended, lets the checks on GitHub run early. On 2026-11-25 this showed that the browser test passes there, which no run in a session can show.
  - The session can refuse an action of a subagent or of the main agent, such as the install of a package that no lock file names. Do not work around it. Tell the owner.

The trial scripts for the SDK are printed at the end of `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`. Never print the key. Do not name the key variable `ANTHROPIC_API_KEY`: the session's own program may read that name. In a cloud session a Claude API key can only be given as an environment variable in the environment's settings, not through the secure form.

## Open items

- One task under "Set the rules" waits for the owner: protect `main` on GitHub. When `main` is protected, the check named `checks` can be made required for merging. The default branch is already `main`.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The real trial of the SDK was one run with one model, and it was not the model now chosen. Not tested with a real model: latency over many runs, long answers, provider errors such as a wrong key or a rate limit, stopping an answer, and changing the settings the runtime chooses. Task 8 of the plan covers part of this.
- The time of a resume was measured with short conversations only. It grows with the length of the conversation. An issue report in the research says that resuming a very large session takes much memory.
- `./scripts/check.sh` takes about 150 seconds and grows with every test that starts the backend. The package `pytest-xdist` (MIT) would run the tests side by side. It was not added. The owner was told on 2026-11-24 and has not asked for it.
- The license of the runtime: the release package holds no license file. That the license of the repository `github/copilot-cli` covers the package is the main agent's inference.
- One package that the SDK brings in, `certifi`, is under MPL-2.0, which the license list of `AGENTS.md` does not name. It is installed and not copied. The owner was told on 2026-11-24.
- Task 7 brought in two more licenses that the list does not name, with installed packages: ISC (`@ungap/structured-clone`, under `react-markdown`) and PSF-2.0 (`greenlet`, under `playwright`, which is MIT and PSF-2.0). The owner accepted both on 2026-11-25.
- The runtime looks at the git repository in the working directory of the backend and stores that directory in the session files. Whether a working directory for each session stops this was not tried.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
- Known limits of the endpoints for conversations, accepted for the first PoC. `docs/tasks.md` has them under task 5.
  - A database error gets the JSON shape of the other errors only when the row of a new conversation cannot be stored. Any other database error gets the plain-text 500 of the framework.
  - A session whose row could not be stored stays on disk. Nothing cleans it up.
  - The project has no tool that changes a table. A change to a table means that the database file is deleted.
  - The list has no paging, and the table has no index on the owner.
- Known limits of sending a message, accepted for the first PoC. `docs/tasks.md` has them under task 6.
  - The title and the time are written before the message reaches the SDK. When the answer fails before that, the conversation has the title of a message that the history does not hold.
  - The "error" message of a stream has one text for every failure. The cause is in the log only.
  - After an error or a stop, the history holds the user's message with no answer under it.
  - The title is cut at a count of code points, which can fall inside a word or an emoji.
  - No test tells apart the two clean-ups that run when the reader of a stream goes away.
  - The reason for the limit on the length of a message is an inference: that the SDK sends a stored message again with every later message. It was not tried.
- Known limits of the agent module, accepted for the first PoC. `docs/tasks.md` has them under task 4.
  - A message that arrives while the history of the same conversation is read is refused as "still answering".
  - An answer that is read in part and then held keeps its conversation busy with no limit. The endpoint of task 6 always reads the answer to its end or closes it.
  - No test fails when a plain error of the SDK is no longer turned into an error of the module.
- The script that creates a user shows a traceback for failures it does not name, such as no input at the password prompt or a database folder that cannot be made. The review of task 2 pointed this out. It was left as it is. Since task 3 this also holds for a secret key that is set and too short.
- Known limits of sign-in, accepted for the first PoC. `docs/tasks.md` has them under task 3.
  - If the database file is made anew while the secret key stays the same, an old token names the new user who got the same id. Change the key together with the database file.
  - Nothing limits how often a sign-in can be tried, or how long a password in a request may be.
  - The backend has no sign-out. A token works until it expires, 8 days by default.
- The test that every endpoint needs a token uses the function `iter_route_contexts` of FastAPI, which the documentation of FastAPI does not describe. If a later version of FastAPI changes it, the test fails and must be written another way.
- That test tries the endpoints only. A request that is answered before it reaches an endpoint is not tried. Task 7 added no such part: the owner chose that the development server passes the calls on. If the backend one day allows the address of a page, look at this then.
- Known limits of the frontend, accepted for the first PoC. `docs/tasks.md` has them under task 7.
  - The way the page reaches the backend is for development only. A deployment needs another part that passes the calls on.
  - Any script on the page can read the token.
  - A stopped or failed answer leaves the page: the history holds no part of it.
  - When the history cannot be read again after a stop, an error or a cut, the user must reload the page.
  - Two quick clicks on "New conversation" make two conversations. A slow read of the list can overwrite a newer one until the next read.
  - A table in an answer shows as plain text. An image in an answer loads from any address: look at this before tools or knowledge sources are added.
  - The types of the answers in `frontend/src/backend.ts` are written by hand. Only the browser test shows that they match the backend, and only for the path it takes.
  - The browser test runs the development server, not a built page.
