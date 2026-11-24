# Current status

Updated 2026-11-24 (US Eastern Time).

## Where the work stands

- The project has three stages so far: setting the rules (done), the technical research (done), and the first PoC (in progress). Use these plain names with the owner. The owner did not agree to short labels for stages and does not want them.
- The first PoC has ten tasks. They are in `docs/tasks.md` under "First PoC", with every design choice and its reason.
- Done so far:
  - Task 1, the skeleton and the automatic checks (pull request #9).
  - The small task before task 2, a check for `docs/architecture.md` (pull request #10).
  - Task 2, the database and the users (pull request #11).
- What task 1 added:
  - `backend/`: a FastAPI application with one endpoint, `/health`. Its dependencies are managed with `uv` and locked in `backend/uv.lock`.
  - `frontend/`: a React and TypeScript application made with `create-vite`, with the demo page removed. Its dependencies are locked in `frontend/package-lock.json`.
  - `scripts/setup.sh` installs the dependencies. `scripts/check.sh` runs every check.
  - `scripts/check_document_map.py` checks that every path in the document map of `AGENTS.md` exists.
  - `.github/workflows/checks.yml` runs `scripts/check.sh` on every pull request and on every push to `main`.
  - A Stop hook in `.claude/settings.json` runs `scripts/check.sh` at the end of every turn of the main agent.
  - `docs/sources.md` records borrowed code.
- What the small task before task 2 added:
  - `scripts/check_architecture.py` checks that every path written in backticks in `docs/architecture.md` exists. It is the second step of `scripts/check.sh`.
  - It catches a file that was renamed or removed while `docs/architecture.md` was not updated. It does not catch a new part that was never drawn. `reviewer` checks that.
  - The check does not read the diagram, because the diagram has no backticks. So the table in `docs/architecture.md` lists every file that the diagram names. Nothing automatic checks that the diagram and the table agree.
- What task 2 added:
  - `backend/app/config.py`: the settings. They are read from environment variables that begin with `POC_`, with the `pydantic-settings` library. The one setting now is the database file. Later tasks add their settings here.
  - `backend/app/database.py`: opens the SQLite file and creates two tables with hand-written SQL. The table of users holds an id, a unique user name, the hash of the password and the time it was made. The table of conversations holds an id as text, the user who owns it, a title and the time it was made.
  - `backend/app/main.py` creates the tables when the backend starts. A later start leaves the data alone.
  - `backend/app/security.py`: turns a password into a one-way hash with Argon2, through the `pwdlib` library, and checks a password against a hash. It follows the official FastAPI full-stack template. `docs/sources.md` has the entry.
  - `backend/app/users.py`: stores a new user. It refuses an empty name, an empty password and a name that exists. It has no other function yet: task 3 adds the lookup that sign-in needs.
  - `backend/app/create_user.py`: the script that creates a user.
  - The table of conversations is made but nothing fills it yet. Task 5 does.
- The title of a conversation (the owner's choice on 2026-11-24): the table of conversations has a `title` column. The title is the opening of the first message. The list of conversations shows it, and shows "New conversation" while there is none. Tasks 5, 6 and 7 each have a line for their part of this in `docs/tasks.md`.
- `docs/architecture.md` shows what is built now in one diagram, down to the file that holds each component, with a table of what each component does. The owner asked for it on 2026-11-24, as one whole picture and not several small ones. The diagram has three groups: the product, the checks, and installing dependencies. Each group has no arrow to another group, because that is what makes Mermaid place them side by side. `implementer` updates it as part of each task and `reviewer` checks it against the code. The rule is in `CLAUDE.md`. The file states its own rules near its top.
- The choices of the first PoC in one line each. The reasons and the accepted costs are in `docs/tasks.md`.
  - Agent layer: the Copilot SDK. It was not compared with other options. All code that touches it stays in one module.
  - The runtime runs inside the backend's own process.
  - The conversation history lives only in the SDK's session files. The application keeps its own table of which user owns which conversation, with a short title.
  - Answers travel to the browser by Server-Sent Events, in the project's own small message format.
  - The frontend is hand-written React components. The code that talks to the backend is one module.
  - Sign-in is a user name and a password with a signed token, kept to the least. It follows the official FastAPI template and stands in for single sign-on.
  - The database is SQLite, with SQL written by hand.
  - The default model is Claude Haiku 5.5, set in configuration.
  - The interface shows the model's reasoning. This is the last building task and is dropped if it proves troublesome.
  - No decision record is written. The choices are cheap to change in a first PoC. The next number is 0007.
- What the owner wants from the project, said on 2026-11-23:
  - Do not make the start complicated.
  - The final platform may serve hundreds of users at once. Three choices of the first PoC do not carry over to that size: where the runtime runs, where the history lives, and the database. `docs/tasks.md` lists this under "Later".
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
- Cloud environments: the project environment allows `github.com`, `release-assets.githubusercontent.com`, `api.anthropic.com` and the package registries. It has one variable and a setup script. The script calls `scripts/setup.sh` when a new machine is built for a session. It works: the sessions of 2026-11-24 started with the dependencies installed.

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

## Next step

1. Task 3 of the plan: sign-in. Start a new session for it, on the project environment `AI-Articheture-Research`.
2. Then the tasks of the plan in order, one at a time. Each brief asks `implementer` to update `docs/architecture.md`, and names the rules written near the top of that file.

For the brief of task 3. The official FastAPI full-stack template was read on 2026-11-24 at commit `77e550a73bb49dd2967622c5ed11bf7a49603c93`, license MIT. Its sign-in part works like this. The token is made with the `pyjwt` library and the algorithm HS256. The token holds the user id in the field `sub` and an expiry time. The secret key and the lifetime of the token are settings. When the user name is unknown, the code still checks the password against a fixed dummy hash, so that the answer takes the same time for a known and an unknown name. Read the template again before borrowing, because it changes.

How to start a session on the project environment: on the screen for starting a new session, the environment selector is the first control in the row under the message box. It is shown only until the first message is sent.

## How to run and verify

- Install the dependencies: `./scripts/setup.sh`. It needs `uv` and `npm`. It installs from the lock files only.
- Run every check: `./scripts/check.sh`. It takes about six seconds. It stops at the first failure and names the failed step. The last line of a good run is "All checks passed."
- If `check.sh` says that the dependencies are not installed, run `./scripts/setup.sh` first.
- Start the backend: `cd backend && uv run uvicorn app.main:app --reload`. Then open `http://127.0.0.1:8000/health` or the generated API documentation at `http://127.0.0.1:8000/docs`. The first start makes the database file and its tables.
- Create a user: `cd backend && uv run python -m app.create_user <user name>`. The script asks for the password twice. It also makes the database file and the tables if they are missing.
  - In a session with no terminal, give the password on standard input, on two lines. Python warns that it cannot hide the input, and the script still works. Use this only for a throwaway user in a trial, with a password made at run time.
- The database file: by default the file `app.db` in the folder `data` inside `backend/`. Git ignores that folder. The variable `POC_DATABASE_FILE` names another file. Give an absolute path: a relative one is read from the folder where the command is started.
- To look inside the database in a cloud session, use Python's `sqlite3` module. The `sqlite3` command-line tool is not installed there.
- Start the frontend: `cd frontend && npm run dev`. The command prints the address to open.
- The backend and the frontend do not talk to each other yet. Task 7 connects them.
- Where the rules of the checks are: `backend/pyproject.toml` for Python, `frontend/eslint.config.js` and the `tsconfig` files for TypeScript.
- A new Python file in `scripts/` must be added to the list `known-first-party` in `backend/pyproject.toml`. Without this, the import-order rule sorts its imports wrongly.
- Run pytest from `backend/` with no path argument, or with `-k`. A path argument outside `backend/` skips the settings, and the tests in `scripts/tests/` then cannot import their modules.
- Backend tests and the database: `backend/tests/conftest.py` gives every test its own database file in a temporary folder. No test may write to the default file.
- Backend tests and passwords: a test makes its passwords at run time, for example with `secrets.token_urlsafe`. Do not write a fixed password in the code, and do not add an exception to the linter's rule against it.
- In `docs/architecture.md`, put only paths that exist in the repository, and addresses of the API that begin with `/`, in backticks. Any other text in backticks fails the check. This includes the path of the database file, which is made at run time, and the names of environment variables. Every file that the diagram names must also be in the table.
- How to draw the diagram of `docs/architecture.md` in a cloud session. This worked on 2026-11-24. Install the `mermaid` package with `npm` into a scratch folder outside the repository. Open a blank page in the browser that comes with the session's Playwright. Load the file `dist/mermaid.min.js` of the package into the page. Call `mermaid.render` with the text of the diagram and take a screenshot. The version was Mermaid 12.3.0. GitHub may draw with another version, so the picture on GitHub is the one that counts.
- A cloud session has a hook of its own that asks for a commit and a push when a turn ends with changes that are not committed or not pushed. Push the work branch before ending a turn.
- A subagent may start in the background even when the call asks for the foreground. The turn of the main agent can then end while the subagent still writes, and the session's hook asks for a commit. Do not commit the unfinished work. Wait for the subagent's report, check the work, then commit.

The trial scripts for the SDK are printed at the end of `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`. Never print the key. Do not name the key variable `ANTHROPIC_API_KEY`: the session's own program may read that name. In a cloud session a Claude API key can only be given as an environment variable in the environment's settings, not through the secure form.

## Open items

- The Stop hook very likely runs in a cloud session, but this is not shown directly. What was seen on 2026-11-24: the session's own record lists two Stop hooks at the end of each turn. The first took about four seconds, which fits `scripts/check.sh`. The second is the session's own reminder to commit and push. A direct proof would be a turn that ends while a check fails.
- One task under "Set the rules" waits for the owner: protect `main` on GitHub. When `main` is protected, the check named `checks` can be made required for merging. The default branch is already `main`.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The real trial of the SDK was one run with one model, and it was not the model now chosen. Not tested: latency over many runs, long answers, provider errors such as a wrong key or a rate limit, and changing the settings the runtime chooses. Task 8 of the plan covers part of this.
- Whether the SDK can stop an answer that is being written is not checked. Task 4 of the plan finds out.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
- The script that creates a user shows a traceback for failures it does not name, such as no input at the password prompt or a database folder that cannot be made. The review of task 2 pointed this out. It was left as it is.
