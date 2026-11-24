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
- What is built, file by file, is in `docs/architecture.md`: one diagram and a table of what each component does. `implementer` updates it as part of each task and `reviewer` checks it against the code. The rule is in `CLAUDE.md`. The file states its own rules near its top.
- What task 1 and the small task after it added, in short:
  - `backend/` is a FastAPI application. Its dependencies are managed with `uv` and locked in `backend/uv.lock`. `frontend/` is a React and TypeScript application made with `create-vite`.
  - `scripts/setup.sh` installs the dependencies. `scripts/check.sh` runs every check. `.github/workflows/checks.yml` runs it on every pull request and on every push to `main`. A Stop hook in `.claude/settings.json` runs it at the end of every turn of the main agent.
  - The check of `docs/architecture.md` reads paths in backticks only. It does not read the diagram. So the table lists every file that the diagram names, and `reviewer` checks that the two agree.
- What task 2 added, in short: the settings, the SQLite file with the tables of users and of conversations, the hash of a password with Argon2, and the script that creates a user. The table of conversations is made but nothing fills it yet. Task 5 does.
- What task 3 added:
  - `backend/app/login.py`: the sign-in endpoint, `POST /login/access-token`. It takes a user name and a password as a form and returns a signed token. A wrong password and an unknown name get the same answer, status 400.
  - `backend/app/protected.py`: the router whose endpoints need a token. Today it holds `GET /users/me`, which returns the id and the name of the signed-in user. **Tasks 5 and 6 add their endpoints to this router.**
  - `backend/app/dependencies.py`: what an endpoint can ask for: the settings, a database connection for this one request, and the signed-in user. A token that is missing or not valid always gets status 401.
  - `backend/app/security.py` now also makes and reads tokens. `backend/app/users.py` now also checks a name and a password and finds a user by id.
  - `backend/app/config.py` has two new settings: the secret key and the lifetime of a token. The function `get_settings()` makes the settings once for each process. Code in the application calls `get_settings()` and does not make its own settings object.
  - `backend/tests/test_every_endpoint_needs_a_token.py`: lists every endpoint of the application. To each one outside a short list of open ones it sends three requests that must be refused. **A pair of method and path is added to that list only when the owner agrees.**
  - `backend/tests/test_requests_at_the_same_time.py`: 60 requests at the same time. It protects the thread setting of the database connection of a request.
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
  - No decision record is written. The choices are cheap to change in a first PoC. The next number is 0007.
- What the owner wants from the project, said on 2026-11-23:
  - Do not make the start complicated.
  - The final platform may serve hundreds of users at once. Three choices of the first PoC do not carry over to that size: where the runtime runs, where the history lives, and the database. `docs/tasks.md` lists this under "Later". The random secret key does not carry over either: with more than one backend process the key must be set.
  - Each team may later have its own frontend. So the backend API and the message format are a contract: written down, and free of anything only one frontend needs.
  - People the owner works with also recommend the Copilot SDK. The owner cannot share their documents. Do not ask for them.
- What the research and the trials found about the SDK, in short. The full account is in `docs/research/reports/第一版 PoC 技术调研.md` and in the trial note next to it.
  - With no GitHub sign-in, the SDK started, streamed an answer, stored the conversation on disk, resumed it and read the history back. This held against a local stand-in and against a real model (one run).
  - The runtime adds its own system prompt. `system_message` with mode "replace" swaps it for the application's own text.
  - With a real model the runtime chooses several request settings by itself: thinking on, effort "medium", an output limit of 48,000 tokens, and prompt-cache markers. Whether the application can change them is not tested.
  - `mode="empty"`, which the vendor advises for shared use, demands an explicit storage directory and an explicit tool list for each session.
  - The application may choose the session id when it creates a session. This is from the vendor's documents and was used in the trial scripts.
  - The SDK has no notion of a user and no lock. Two requests on one conversation at the same time are undefined.
  - Under BYOK the SDK reports a cost of 0. The application must work out cost from the token counts.
  - The SDK changes fast. Versions must be pinned.
- Model key: the project environment `AI-Articheture-Research` holds a Claude API key as the variable `POC_MODEL_API_KEY`. Only task 8 uses it. The automatic checks need no key. The name begins with `POC_` like the settings. The settings class reads only the variables it has a field for, so it does not read the key today. Task 4 decides how the key reaches the SDK.
- Cloud environments: the project environment allows `github.com`, `release-assets.githubusercontent.com`, `api.anthropic.com` and the package registries. It has one variable and a setup script. The script calls `scripts/setup.sh` when a new machine is built for a session.
  - Seen on 2026-11-24: the session for task 3 started with the packages from before task 2. The checks failed at the mypy step with "Cannot find implementation or library stub". `./scripts/setup.sh` fixed it. Run it at the start of a session when a check fails this way.

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
- A choice can be asked with the question form of the session, with the recommended option first. The owner answered the two choices of task 3 this way.

## Next step

1. Task 4 of the plan: the module that touches the SDK. Start a new session for it, on the project environment `AI-Articheture-Research`.
2. Then the tasks of the plan in order, one at a time. Each brief asks `implementer` to update `docs/architecture.md`, and names the rules written near the top of that file.

For task 4. Read the research report and the trial note first. Before the brief, list for the owner the choices that have more than one workable option, each with its cost and a recommendation. The main agent's guess at what they are, not checked: how the model key reaches the SDK; where the storage directory of the sessions is; what the project's own system prompt says; how the module lets only one message at a time into a conversation. The new settings go into `backend/app/config.py`. The SDK is a new package: pin its version and check its license first. The trial scripts at the end of the trial note show calls that worked.

For task 5. The endpoints go on the router in `backend/app/protected.py`. An endpoint gets the signed-in user by asking for `CurrentUser` and a database connection by asking for `ConnectionDependency`, both from `backend/app/dependencies.py`. The connection of a request is closed at the end with no commit, so code that writes must commit, for example with `with connection:`. Use status 404 for a conversation that is not the user's. Status 401 is kept for "sign in again".

How to start a session on the project environment: on the screen for starting a new session, the environment selector is the first control in the row under the message box. It is shown only until the first message is sent.

## How to run and verify

- Install the dependencies: `./scripts/setup.sh`. It needs `uv` and `npm`. It installs from the lock files only.
- Run every check: `./scripts/check.sh`. It takes about nine seconds. It stops at the first failure and names the failed step. The last line of a good run is "All checks passed."
- Start the backend: `cd backend && uv run uvicorn app.main:app --reload`. Then open `http://127.0.0.1:8000/health` or the generated API documentation at `http://127.0.0.1:8000/docs`. The first start makes the database file and its tables.
- Create a user: `cd backend && uv run python -m app.create_user <user name>`. The script asks for the password twice. It also makes the database file and the tables if they are missing.
  - In a session with no terminal, give the password on standard input, on two lines. Python warns that it cannot hide the input, and the script still works. Use this only for a throwaway user in a trial, with a password made at run time.
- Sign in by hand: on the page `/docs`, press "Authorize" and give the user name and the password. The page then sends the token with every request, and `/users/me` can be tried there. From a command line, send the form fields `username` and `password` to `POST /login/access-token`, and send the token in the header `Authorization: Bearer <token>`.
- The secret key: with no variable, every start of the backend makes a new key, and the tokens from before are refused. With `--reload`, every saved change to the backend code is a restart. To keep the tokens, set `POC_TOKEN_SECRET_KEY` to a random text of at least 32 characters. Never write a key into a file of the repository.
- The database file: by default the file `app.db` in the folder `data` inside `backend/`. Git ignores that folder. The variable `POC_DATABASE_FILE` names another file. Give an absolute path: a relative one is read from the folder where the command is started.
- To look inside the database in a cloud session, use Python's `sqlite3` module. The `sqlite3` command-line tool is not installed there.
- Start the frontend: `cd frontend && npm run dev`. The command prints the address to open.
- The backend and the frontend do not talk to each other yet. Task 7 connects them.
- Where the rules of the checks are: `backend/pyproject.toml` for Python, `frontend/eslint.config.js` and the `tsconfig` files for TypeScript.
- A new Python file in `scripts/` must be added to the list `known-first-party` in `backend/pyproject.toml`. Without this, the import-order rule sorts its imports wrongly.
- Run pytest from `backend/` with no path argument, or with `-k`. A path argument outside `backend/` skips the settings, and the tests in `scripts/tests/` then cannot import their modules.
- Backend tests:
  - `backend/tests/conftest.py` gives every test its own database file in a temporary folder and its own settings. No test may write to the default file.
  - The same file has three helpers: `client` starts the application, `add_user` stores a user with a password made at run time, and `sign_in` returns a token for that user.
  - A test makes its passwords and keys at run time, for example with `secrets.token_urlsafe`. Do not write a fixed password or key in the code, and do not add an exception to the linter's rule against it. That rule also flags a fixed text that is given to, or compared with, a name that has the word "token" in it, such as the token type "bearer". The code avoids this without an exception: see the model `Token` in `backend/app/login.py`.
- How to show that a test catches a fault, with no change to a file of the repository. This worked on 2026-11-24. Write a small Python file in a scratch folder that imports the application and adds the faulty part in memory. Run pytest from `backend/` with that folder and `.` in `PYTHONPATH`, and name the file with the option `-p`.
- In `docs/architecture.md`, put only paths that exist in the repository, and addresses of the API that begin with `/`, in backticks. Any other text in backticks fails the check. This includes the path of the database file, which is made at run time, and the names of environment variables. Every file that the diagram names must also be in the table.
- How to draw the diagram of `docs/architecture.md` in a cloud session. This worked on 2026-11-24. Install the `mermaid` package with `npm` into a scratch folder outside the repository. Open a blank page in the browser that comes with the session's Playwright. Load the file `dist/mermaid.min.js` of the package into the page. Call `mermaid.render` with the text of the diagram and take a screenshot. The version was Mermaid 12.3.0. GitHub may draw with another version, so the picture on GitHub is the one that counts.
- A cloud session has a hook of its own that asks for a commit and a push when a turn ends with changes that are not committed or not pushed. Push the work branch before ending a turn.
- The Stop hook of the project runs in a cloud session too. Shown on 2026-11-24: a turn ended while `implementer` was still writing, and the hook reported the failed check.
- Subagents:
  - A subagent may start in the background even when the call asks for the foreground. On 2026-11-24 every one did. The turn of the main agent then ends while the subagent still writes. The Stop hook reports failed checks and the session's hook asks for a commit. Do neither. Wait for the subagent's report, check the work, then commit.
  - Write each brief to a file in the scratch folder and give the subagent the path. `reviewer` then reads the same brief that `implementer` worked from.
  - For a round of fixes, or a second review round, send a message to the same subagent. It keeps what it has read. This worked on 2026-11-24.

The trial scripts for the SDK are printed at the end of `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`. Never print the key. Do not name the key variable `ANTHROPIC_API_KEY`: the session's own program may read that name. In a cloud session a Claude API key can only be given as an environment variable in the environment's settings, not through the secure form.

## Open items

- One task under "Set the rules" waits for the owner: protect `main` on GitHub. When `main` is protected, the check named `checks` can be made required for merging. The default branch is already `main`.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The real trial of the SDK was one run with one model, and it was not the model now chosen. Not tested: latency over many runs, long answers, provider errors such as a wrong key or a rate limit, and changing the settings the runtime chooses. Task 8 of the plan covers part of this.
- Whether the SDK can stop an answer that is being written is not checked. Task 4 of the plan finds out.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
- The script that creates a user shows a traceback for failures it does not name, such as no input at the password prompt or a database folder that cannot be made. The review of task 2 pointed this out. It was left as it is. Since task 3 this also holds for a secret key that is set and too short.
- Known limits of sign-in, accepted for the first PoC. `docs/tasks.md` has them under task 3.
  - If the database file is made anew while the secret key stays the same, an old token names the new user who got the same id. Change the key together with the database file.
  - Nothing limits how often a sign-in can be tried, or how long a password in a request may be.
  - The backend has no sign-out. A token works until it expires, 8 days by default.
- The test that every endpoint needs a token uses the function `iter_route_contexts` of FastAPI, which the documentation of FastAPI does not describe. If a later version of FastAPI changes it, the test fails and must be written another way.
- That test tries the endpoints only. A request that is answered before it reaches an endpoint is not tried. Task 7 may add such a part, to let the browser page call the backend from another address. Look at this then.
