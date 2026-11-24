# Current status

Updated 2026-11-24 (US Eastern Time).

## Where the work stands

- The project has three stages so far: setting the rules (done), the technical research (done), and the first PoC (in progress). Use these plain names with the owner. The owner did not agree to short labels for stages and does not want them.
- The first PoC has ten tasks. They are in `docs/tasks.md` under "First PoC", with every design choice and its reason.
- Task 1, the skeleton and the automatic checks, is done (pull request #9).
- What task 1 added:
  - `backend/`: an empty FastAPI application with one endpoint, `/health`. Its dependencies are managed with `uv` and locked in `backend/uv.lock`.
  - `frontend/`: a React and TypeScript application made with `create-vite`, with the demo page removed. Its dependencies are locked in `frontend/package-lock.json`.
  - `scripts/setup.sh` installs the dependencies. `scripts/check.sh` runs every check.
  - `scripts/check_document_map.py` checks that every path in the document map of `AGENTS.md` exists.
  - `.github/workflows/checks.yml` runs `scripts/check.sh` on every pull request and on every push to `main`.
  - A Stop hook in `.claude/settings.json` runs `scripts/check.sh` at the end of every turn of the main agent.
  - `docs/sources.md` records borrowed code. The `create-vite` template is its first entry.
- `docs/architecture.md` shows what is built now in one diagram, down to the file that holds each component, with a table of what each component does. The owner asked for it on 2026-11-24, as one whole picture and not several small ones. The diagram has three groups: the product, the checks, and installing dependencies. Each group has no arrow to another group, because that is what makes Mermaid place them side by side. Its diagrams are Mermaid text, which GitHub draws. `implementer` updates it as part of each task and `reviewer` checks it against the code. The rule is in `CLAUDE.md`.
- The choices of the first PoC in one line each. The reasons and the accepted costs are in `docs/tasks.md`.
  - Agent layer: the Copilot SDK. It was not compared with other options. All code that touches it stays in one module.
  - The runtime runs inside the backend's own process.
  - The conversation history lives only in the SDK's session files. The application keeps its own table of which user owns which conversation.
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
  - The SDK has no notion of a user and no lock. Two requests on one conversation at the same time are undefined.
  - Under BYOK the SDK reports a cost of 0. The application must work out cost from the token counts.
  - The SDK changes fast. Versions must be pinned.
- Model key: the project environment `AI-Articheture-Research` holds a Claude API key as the variable `POC_MODEL_API_KEY`. Only task 8 uses it. The automatic checks need no key.
- Cloud environments: the project environment allows `github.com`, `release-assets.githubusercontent.com`, `api.anthropic.com` and the package registries. It has one variable and a setup script. The script calls `scripts/setup.sh` when a new machine is built for a session. The owner approved it on 2026-11-23.

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
- The owner watches the usage of the main model. Keep each session to one task. Long explanations belong in a separate session. Do not suggest a new subagent when the main agent or `implementer` can do the work for less.
- The owner plans to run the trial of task 8 in the browser in person. Whether the owner writes any part by hand is the owner's choice. Do not set exercises.

## Next step

1. The small task before task 2 in `docs/tasks.md`: a check that every path named in `docs/architecture.md` exists. Start a new session for it, on the project environment `AI-Articheture-Research`.
2. Task 2 of the plan: the database and the users.
3. Then the tasks of the plan in order, one at a time. Each brief asks `implementer` to update `docs/architecture.md`.

How to start a session on the project environment: on the screen for starting a new session, the environment selector is the first control in the row under the message box. It is shown only until the first message is sent.

## How to run and verify

- Install the dependencies: `./scripts/setup.sh`. It needs `uv` and `npm`. It installs from the lock files only.
- Run every check: `./scripts/check.sh`. It takes about six seconds. It stops at the first failure and names the failed step. The last line of a good run is "All checks passed."
- If `check.sh` says that the dependencies are not installed, run `./scripts/setup.sh` first.
- Start the backend: `cd backend && uv run uvicorn app.main:app --reload`. Then open `http://127.0.0.1:8000/health` or the generated API documentation at `http://127.0.0.1:8000/docs`.
- Start the frontend: `cd frontend && npm run dev`. The command prints the address to open.
- The backend and the frontend do not talk to each other yet. Task 7 connects them.
- Where the rules of the checks are: `backend/pyproject.toml` for Python, `frontend/eslint.config.js` and the `tsconfig` files for TypeScript.
- A new Python file in `scripts/` must be added to the list `known-first-party` in `backend/pyproject.toml`. Without this, the import-order rule sorts its imports wrongly.
- Run pytest from `backend/` with no path argument, or with `-k`. A path argument outside `backend/` skips the settings, and the tests in `scripts/tests/` then cannot import their modules.

The trial scripts for the SDK are printed at the end of `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`. Never print the key. Do not name the key variable `ANTHROPIC_API_KEY`: the session's own program may read that name. In a cloud session a Claude API key can only be given as an environment variable in the environment's settings, not through the secure form.

## Open items

- The setup script of the cloud environment is saved but not proven. It first runs when a new session starts. Check in the next session whether the dependencies are already installed: `./scripts/check.sh` says so. If they are not, `./scripts/setup.sh` installs them in a few seconds. One known cause: the first new session after the script was saved builds a stored copy of the machine, and that copy holds the dependencies only if `scripts/setup.sh` was on `main` by then. The copy is rebuilt after about seven days, or when the script changes.
- The Stop hook has been run by hand and by tests. Whether Claude Code runs it at the end of a turn in a cloud session will show in the next session.
- One task under "Set the rules" waits for the owner: protect `main` on GitHub. When `main` is protected, the check named `checks` can be made required for merging. The default branch is already `main`.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The real trial of the SDK was one run with one model, and it was not the model now chosen. Not tested: latency over many runs, long answers, provider errors such as a wrong key or a rate limit, and changing the settings the runtime chooses. Task 8 of the plan covers part of this.
- Whether the SDK can stop an answer that is being written is not checked. Task 4 of the plan finds out.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
