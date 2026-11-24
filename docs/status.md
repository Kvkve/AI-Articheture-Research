# Current status

Updated 2026-11-24 (US Eastern Time).

## Where the work stands

- The project has three stages so far: setting the rules (done), the technical research (done), and the first PoC (in progress). Use these plain names with the owner. The owner did not agree to short labels for stages and does not want them.
- The first PoC has ten tasks. They are in `docs/tasks.md` under "First PoC", with every design choice and its reason.
- Done so far:
  - Task 1, the skeleton and the automatic checks (pull request #9).
  - The small task before task 2, a check for `docs/architecture.md` (pull request #10).
  - Task 2, the database and the users (pull request #11).
  - Task 3, sign-in (pull request #12).
  - Task 4, the module that touches the SDK (pull request #13).
- What is built, file by file, is in `docs/architecture.md`: one diagram and a table of what each component does. `implementer` updates it as part of each task and `reviewer` checks it against the code. The rule is in `CLAUDE.md`. The file states its own rules near its top.
- What tasks 1 to 3 added, in short:
  - `backend/` is a FastAPI application. Its dependencies are managed with `uv` and locked in `backend/uv.lock`. `frontend/` is a React and TypeScript application made with `create-vite`.
  - `scripts/setup.sh` installs the dependencies. `scripts/check.sh` runs every check. `.github/workflows/checks.yml` runs it on every pull request and on every push to `main`. A Stop hook in `.claude/settings.json` runs it at the end of every turn of the main agent.
  - The check of `docs/architecture.md` reads paths in backticks only. It does not read the diagram. So the table lists every file that the diagram names, and `reviewer` checks that the two agree.
  - The settings, the SQLite file with the tables of users and of conversations, the hash of a password with Argon2, and the script that creates a user. The table of conversations is made but nothing fills it yet. Task 5 does.
  - Sign-in. `backend/app/login.py` holds the sign-in endpoint. `backend/app/protected.py` holds the router whose endpoints need a token: **tasks 5 and 6 add their endpoints to this router.** `backend/app/dependencies.py` holds what an endpoint can ask for. A token that is missing or not valid always gets status 401.
  - `backend/tests/test_every_endpoint_needs_a_token.py` lists every endpoint of the application. To each one outside a short list of open ones it sends three requests that must be refused. **A pair of method and path is added to that list only when the owner agrees.**
- What task 4 added:
  - `backend/app/agent.py`: the only file that imports the Copilot SDK. A rule of ruff in `backend/pyproject.toml` fails the checks when another Python file in `backend/` or `scripts/` imports it. No type of the SDK leaves the module: it gives out its own small types and raises its own errors.
  - The module has one class, `Agent`. One object serves one backend process. `backend/app/main.py` makes it when the backend starts, starts the runtime of the SDK, and stops it at shut-down. An endpoint asks for it with `AgentDependency` from `backend/app/dependencies.py`. **No endpoint uses it yet. The backend API is the same as after task 3.**
  - Its three actions, all `async`:
    - `start_conversation()` makes a session on disk and returns its id, 32 random hexadecimal characters.
    - `begin_answer(conversation_id, text)` is step one of sending. It returns an `Answer`. Reading the `Answer` with `async for` is step two and gives the pieces of text.
    - `read_history(conversation_id)` returns a list of `HistoryMessage`, each with a role, "user" or "assistant", and a text.
  - Its errors. All are subclasses of `AgentError`: `InvalidConversationIdError`, `UnknownConversationError`, `ConversationBusyError`, `NoModelKeyError`, `ModelProviderError` (it has a `status_code`), and `AnswerTimedOutError`.
  - `backend/app/config.py` has seven new settings: the model key, the model name, the provider type and address, the folder of the session files, the system prompt, and the longest wait for the next part of an answer.
  - `backend/tests/model_stand_in.py`: a local server that stands in for the model provider in the tests. It speaks the streaming format of the Anthropic Messages API and records the requests it gets.
  - `scripts/setup.sh` also downloads the runtime of the SDK, about 196 MB unpacked, into a cache folder outside the repository.
- The title of a conversation (the owner's choice on 2026-11-24): the table of conversations has a `title` column. The title is the opening of the first message. The list of conversations shows it, and shows "New conversation" while there is none. Tasks 5, 6 and 7 each have a line for their part of this in `docs/tasks.md`.
- The choices of the first PoC in one line each. The reasons and the accepted costs are in `docs/tasks.md`.
  - Agent layer: the Copilot SDK. It was not compared with other options. All code that touches it stays in one module.
  - The runtime runs inside the backend's own process.
  - The conversation history lives only in the SDK's session files. The application keeps its own table of which user owns which conversation, with a short title.
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
- Model key: the project environment `AI-Articheture-Research` holds a Claude API key as the variable `POC_MODEL_API_KEY`. Since task 4 the settings class reads it. So a backend that is started by hand in a session on that environment has the real key and the real provider address. No endpoint sends a message yet. From task 6 on, a message sent to such a backend calls the real model and costs money. The tests are safe: `backend/tests/conftest.py` removes the key and the other model variables before every test. Only task 8 means to call the real model.
- Cloud environments: the project environment allows `github.com`, `release-assets.githubusercontent.com`, `api.anthropic.com` and the package registries. It has one variable and a setup script. The script calls `scripts/setup.sh` when a new machine is built for a session.
  - Seen on 2026-11-24, in the sessions for task 3 and for task 4: the session started with the packages from before the last tasks. The checks failed at the mypy step with "Cannot find implementation or library stub". `./scripts/setup.sh` fixed it. Run it at the start of a session when a check fails this way.

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
- A choice can be asked with the question form of the session, with the recommended option first. The owner answered the two choices of task 3 and the four choices of task 4 this way, and took the recommended option each time.

## Next step

1. Task 5 of the plan: conversations. Start a new session for it, on the project environment `AI-Articheture-Research`.
2. Then the tasks of the plan in order, one at a time. Each brief asks `implementer` to update `docs/architecture.md`, and names the rules written near the top of that file.

For task 5. Before the brief, list for the owner the choices that have more than one workable option. The main agent's guess at what they are, not checked: the addresses of the three endpoints; what the list gives for each conversation and in which order; what happens to a session on disk when its row cannot be stored.

- The endpoints go on the router in `backend/app/protected.py`. An endpoint gets the signed-in user by asking for `CurrentUser`, a database connection by asking for `ConnectionDependency`, and the agent by asking for `AgentDependency`, all from `backend/app/dependencies.py`.
- The actions of the agent are `async`. An endpoint that calls them must be `async def`.
- The connection of a request is closed at the end with no commit, so code that writes must commit, for example with `with connection:`.
- Use status 404 for a conversation that is not the user's. Status 401 is kept for "sign in again". Check the ownership table before every call to the agent with a conversation id.
- The id of a new conversation comes from `start_conversation()` of the agent. The same value is the key of the row in the table of conversations.
- The fixtures `stand_in`, `stand_in_address` and `model_key` are in `backend/tests/test_agent.py`. Move them to `backend/tests/conftest.py` when the tests of another file need them.

For task 6. Sending has two steps: `begin_answer` and then reading the `Answer`. The endpoint does step one before it starts the stream, so that it can refuse a message with a status code. It must read the answer to its end or close it, or the conversation stays busy. The module stops the model by itself when the task that reads the answer is cancelled, which is what a browser that leaves does. Which status code each error of the module gets is a choice for the owner.

How to start a session on the project environment: on the screen for starting a new session, the environment selector is the first control in the row under the message box. It is shown only until the first message is sent.

## How to run and verify

- Install the dependencies: `./scripts/setup.sh`. It needs `uv` and `npm`. It installs from the lock files only. Then it downloads the runtime of the SDK from `github.com`, if the cache does not hold it yet.
- Run every check: `./scripts/check.sh`. It takes about 80 seconds: the tests stop the runtime of the SDK about 60 times, and each stop takes one second inside the SDK. Every later test that starts the backend adds one second. It stops at the first failure and names the failed step. The last line of a good run is "All checks passed."
- Start the backend: `cd backend && uv run uvicorn app.main:app --reload`. Then open `http://127.0.0.1:8000/health` or the generated API documentation at `http://127.0.0.1:8000/docs`. The first start makes the database file and its tables, and the folder of the session files.
- Create a user: `cd backend && uv run python -m app.create_user <user name>`. The script asks for the password twice. It also makes the database file and the tables if they are missing.
  - In a session with no terminal, give the password on standard input, on two lines. Python warns that it cannot hide the input, and the script still works. Use this only for a throwaway user in a trial, with a password made at run time.
- Sign in by hand: on the page `/docs`, press "Authorize" and give the user name and the password. The page then sends the token with every request, and `/users/me` can be tried there. From a command line, send the form fields `username` and `password` to `POST /login/access-token`, and send the token in the header `Authorization: Bearer <token>`.
- The secret key: with no variable, every start of the backend makes a new key, and the tokens from before are refused. With `--reload`, every saved change to the backend code is a restart. To keep the tokens, set `POC_TOKEN_SECRET_KEY` to a random text of at least 32 characters. Never write a key into a file of the repository.
- Where the data is. By default both places are in the folder `data` inside `backend/`. Git ignores that folder.
  - The database file is `app.db`. The variable `POC_DATABASE_FILE` names another file.
  - The session files of the SDK are in the folder `sessions`, one folder for each conversation, as plain text. The variable `POC_SESSION_DIRECTORY` names another folder.
  - Give absolute paths: a relative one is read from the folder where the command is started.
  - The two belong together. A row of the table of conversations names a session folder. Delete or move both, not one.
- The model settings: `POC_MODEL_API_KEY`, `POC_MODEL_NAME`, `POC_MODEL_PROVIDER_TYPE`, `POC_MODEL_PROVIDER_ADDRESS`, `POC_SYSTEM_PROMPT` and `POC_ANSWER_WAIT_SECONDS`. The defaults are in `backend/app/config.py`.
- To look inside the database in a cloud session, use Python's `sqlite3` module. The `sqlite3` command-line tool is not installed there.
- Start the frontend: `cd frontend && npm run dev`. The command prints the address to open.
- The backend and the frontend do not talk to each other yet. Task 7 connects them.
- Where the rules of the checks are: `backend/pyproject.toml` for Python, `frontend/eslint.config.js` and the `tsconfig` files for TypeScript.
- A new Python file in `scripts/` must be added to the list `known-first-party` in `backend/pyproject.toml`. Without this, the import-order rule sorts its imports wrongly.
- Run pytest from `backend/` with no path argument, or with `-k`. A path argument outside `backend/` skips the settings, and the tests in `scripts/tests/` then cannot import their modules.
- Backend tests:
  - `backend/tests/conftest.py` gives every test its own database file and its own session folder in a temporary folder, and its own settings. No test may write to the default places. It removes the token variables and the model variables of the machine before every test.
  - The same file has three helpers: `client` starts the application, `add_user` stores a user with a password made at run time, and `sign_in` returns a token for that user. Starting the application starts the runtime of the SDK, and stopping it costs one second.
  - A test makes its passwords and keys at run time, for example with `secrets.token_urlsafe`. Do not write a fixed password or key in the code, and do not add an exception to the linter's rule against it. That rule also flags a fixed text that is given to, or compared with, a name that has the word "token" in it, such as the token type "bearer". The code avoids this without an exception: see the model `Token` in `backend/app/login.py`.
  - The tests of the agent run the real SDK and runtime against the stand-in. The runtime follows the proxy variables of the machine, so the fixture `stand_in_address` removes them. A test steers the stand-in with events and not with waits of a fixed length.
  - A test may not import the SDK. To see whether a session of the SDK is still open, one test reads private state of the SDK's client through the agent object, and says so in a comment.
  - pytest has no plugin for `async def` tests here. A test of the agent is a plain function that runs its steps with `asyncio.run()`. A test that starts the application calls the agent through the `portal` of the test client.
- How to show that a test catches a fault, with no change to a file of the repository. This worked on 2026-11-24. Write a small Python file in a scratch folder that imports the application and adds the faulty part in memory. Run pytest from `backend/` with that folder and `.` in `PYTHONPATH`, and name the file with the option `-p`.
- In `docs/architecture.md`, put only paths that exist in the repository, and addresses of the API that begin with `/`, in backticks. Any other text in backticks fails the check. This includes the path of the database file, which is made at run time, and the names of environment variables. Every file that the diagram names must also be in the table.
- How to draw the diagram of `docs/architecture.md` in a cloud session. This worked on 2026-11-24. Install the `mermaid` package with `npm` into a scratch folder outside the repository. Open a blank page in the browser that comes with the session's Playwright. Load the file `dist/mermaid.min.js` of the package into the page. Call `mermaid.render` with the text of the diagram and take a screenshot. The version was Mermaid 12.3.0. GitHub may draw with another version, so the picture on GitHub is the one that counts.
- A cloud session has a hook of its own that asks for a commit and a push when a turn ends with changes that are not committed or not pushed. Push the work branch before ending a turn.
- The Stop hook of the project runs in a cloud session too. Shown on 2026-11-24: a turn ended while `implementer` was still writing, and the hook reported the failed check.
- Subagents:
  - A subagent may start in the background even when the call asks for the foreground. On 2026-11-24 every one did. The turn of the main agent then ends while the subagent still writes. The Stop hook reports failed checks and the session's hook asks for a commit. Do neither. Wait for the subagent's report, check the work, then commit.
  - Write each brief to a file in the scratch folder and give the subagent the path. `reviewer` then reads the same brief that `implementer` worked from. Add each round of changes to the end of that file.
  - For a round of fixes, or a second review round, send a message to the same subagent. It keeps what it has read. This worked on 2026-11-24.
  - A limit in a brief that is not in the acceptance criteria of `docs/tasks.md` can stop `implementer`. On 2026-11-24 a time limit for the checks did. Say in the brief which points come from `docs/tasks.md` and which the main agent added.

The trial scripts for the SDK are printed at the end of `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`. Never print the key. Do not name the key variable `ANTHROPIC_API_KEY`: the session's own program may read that name. In a cloud session a Claude API key can only be given as an environment variable in the environment's settings, not through the secure form.

## Open items

- One task under "Set the rules" waits for the owner: protect `main` on GitHub. When `main` is protected, the check named `checks` can be made required for merging. The default branch is already `main`.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The real trial of the SDK was one run with one model, and it was not the model now chosen. Not tested with a real model: latency over many runs, long answers, provider errors such as a wrong key or a rate limit, stopping an answer, and changing the settings the runtime chooses. Task 8 of the plan covers part of this.
- The time of a resume was measured with short conversations only. It grows with the length of the conversation. An issue report in the research says that resuming a very large session takes much memory.
- `./scripts/check.sh` takes about 80 seconds and grows with every test that starts the backend. The package `pytest-xdist` (MIT) would run the tests side by side. It was not added. The owner was told on 2026-11-24 and has not asked for it.
- The license of the runtime: the release package holds no license file. That the license of the repository `github/copilot-cli` covers the package is the main agent's inference.
- One package that the SDK brings in, `certifi`, is under MPL-2.0, which the license list of `AGENTS.md` does not name. It is installed and not copied. The owner was told on 2026-11-24.
- The runtime looks at the git repository in the working directory of the backend and stores that directory in the session files. Whether a working directory for each session stops this was not tried.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
- Known limits of the agent module, accepted for the first PoC. `docs/tasks.md` has them under task 4.
  - A message that arrives while the history of the same conversation is read is refused as "still answering".
  - An answer that is read in part and then held keeps its conversation busy with no limit.
  - No test fails when a plain error of the SDK is no longer turned into an error of the module.
- The script that creates a user shows a traceback for failures it does not name, such as no input at the password prompt or a database folder that cannot be made. The review of task 2 pointed this out. It was left as it is. Since task 3 this also holds for a secret key that is set and too short.
- Known limits of sign-in, accepted for the first PoC. `docs/tasks.md` has them under task 3.
  - If the database file is made anew while the secret key stays the same, an old token names the new user who got the same id. Change the key together with the database file.
  - Nothing limits how often a sign-in can be tried, or how long a password in a request may be.
  - The backend has no sign-out. A token works until it expires, 8 days by default.
- The test that every endpoint needs a token uses the function `iter_route_contexts` of FastAPI, which the documentation of FastAPI does not describe. If a later version of FastAPI changes it, the test fails and must be written another way.
- That test tries the endpoints only. A request that is answered before it reaches an endpoint is not tried. Task 7 may add such a part, to let the browser page call the backend from another address. Look at this then.
