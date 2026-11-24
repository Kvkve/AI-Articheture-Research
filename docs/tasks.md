# Task list

Marks: `[ ]` not started, `[~]` in progress, `[x]` done.

## Set the rules

- [x] Research workflows and repository conventions for AI-assisted development
- [x] Write the project rules, document structure, agent roles and decisions 0001 to 0005
- [x] Write the project background in `README.md`
- [x] Owner reads the English files
- [x] Remove decision records 0001 to 0006 (the owner's choice on 2026-11-23). They held working rules, which stay in `AGENTS.md` and `CLAUDE.md`. Decision records are now only for product design choices that are costly to change
- [ ] Owner sets the default branch to `main` on GitHub
- [ ] Owner protects `main` on GitHub: changes only through a pull request
- [x] Check that the limits in `.claude/settings.json` are loaded in a new session (both variables are present)
- [x] Test that the concurrent limit is enforced: on 2026-11-23, with the owner's approval, four trivial subagents were started at once. Three ran at the same time and the fourth was refused with "Concurrent subagent limit reached"
- [x] Test that nesting is off: on 2026-11-23, with the owner's approval, a `general-purpose` subagent was asked to start another. It reported that its tool list has no tool for starting subagents, so it could not even try. The outcome is "tool absent", not "call refused". The test does not show whether the setting or the tool's default removes it

## Technical research

Plan (approved by the owner on 2026-11-23): three `researcher` subagents on Sonnet in parallel, then one report written by a subagent on Opus.

- [x] Researcher 1, GitHub Copilot SDK basics: setup with your own model API key, the Python API, streaming output, current limits and preview status. Notes: `docs/research/research_notes/第一版 PoC 技术调研/copilot_sdk_basics.md`
- [x] Researcher 2, GitHub Copilot SDK for several users: session persistence and resume, isolation between users, deployment shapes (one runtime per user or a shared one). Notes: `docs/research/research_notes/第一版 PoC 技术调研/copilot_sdk_multi_user.md`
- [x] Researcher 3, open-source components to borrow: frontend and backend scaffolding, chat interface components, conventions for streaming between backend and frontend; the license and maintenance state of each. Notes: `docs/research/research_notes/第一版 PoC 技术调研/open_source_components.md`
- [x] One report in Chinese for the owner, with sources: `docs/research/reports/第一版 PoC 技术调研.md`
- [x] First concept lesson for the owner, built on the report and starting from the data model: what an API is, what a session is, what streaming is. Given in conversation on 2026-11-23, with the owner's follow-up questions answered. The owner's change to the teaching rules on the same day withdrew its explain-back questions and its exercise
- [x] Trial run of the SDK without a model key, against a local stand-in provider (2026-11-23). Notes: `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`
- [x] Trial run with a real model provider: one chat turn, once the owner has chosen the provider and supplied a key through the secure form. Done on 2026-11-23 with one difference from this wording: the key was given as the environment variable `POC_MODEL_API_KEY`, not through a form, because a form cannot carry this kind of key (see `docs/status.md`). The owner accepted this difference on 2026-11-23. The run used Anthropic, the model `claude-opus-5-5`, and two chat turns with a disconnect and a resume between them. The provider's data terms were checked first. Notes: the section "Third run: a real model provider" in `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`
- [x] Create the cloud environment `AI-Articheture-Research` for this project only (2026-11-23). The plan was to enter the model key there. For the trial the key was set on the owner's Default environment instead; see `docs/status.md`
- [x] Write the plan and acceptance criteria for the first PoC, for the owner to review (2026-11-23). It is under "First PoC", in the part "Plan"

## First PoC

Goal: a simple frontend and backend; chat with a model through an API key; several users; several conversations per user.

### Choices

The owner made every choice below in conversation. Each paragraph gives the choice, the reason and the cost that was accepted.

Agent layer (chosen by the owner on 2026-11-23): the first PoC uses the Copilot SDK. The reasons: it is the SDK this project set out to study; three trial runs, the last one against a real model, showed that it works with the project's own model key; people the owner works with also recommend it, and the first PoC is meant as a reference for a later build in that setting. It was not compared with other options. All code that touches the SDK stays in one module, so that the SDK can be replaced. No decision record is written now, because the choice is cheap to change in a first PoC.

Where the runtime runs (chosen by the owner on 2026-11-23): inside the backend's own process. This is the SDK's default and the only way the trial runs tested. A crash of the runtime then stops the backend and every conversation in progress. That is accepted for a first PoC on one machine. The connection type is set in the one module that touches the SDK, so it can be changed to a child process later.

Where the conversation history lives (chosen by the owner on 2026-11-23): only in the SDK's session files on the backend's disk. The backend reads the history back through the SDK. The application keeps its own table of which user owns which conversation, and checks it before every action on a conversation. The trial runs tested storing, resuming and reading back. The cost: the content cannot be queried with SQL, and the vendor decides the file format. A copy in the application's own database can be added later in the one module that touches the SDK.

How answers travel from the backend to the browser (chosen by the owner on 2026-11-23): Server-Sent Events. One direction is enough for question-and-answer chat. FastAPI has it built in. The ready-made chat formats that the research found are built on it, so the choice fits a hand-written frontend and a component library alike. What each message holds is chosen together with the frontend. This project has not run any of the transport options yet.

The frontend (chosen by the owner on 2026-11-23): hand-written React components. One small library, `react-markdown`, shows the formatting of answers. The message format over Server-Sent Events is the project's own and stays small. The reasons: every step of the path stays in the project's own code, and there is no second fast-changing dependency next to the SDK. The cost: a plain interface, and the project writes the stop button, the scrolling and the error display itself. The owner hopes that each team can later have its own frontend. So the backend API and the message format are a contract: they are written down, and they hold nothing that only this one frontend needs. In the frontend, the code that talks to the backend stays in one module, apart from the components that draw the page.

Where the project skeleton comes from (chosen by the owner on 2026-11-23): the frontend skeleton is made with `create-vite`, and the backend is a hand-written FastAPI application. The sign-in part follows the way of the official FastAPI full-stack template and is not invented here. The reasons: the skeleton stays small, and sign-in is the one part where a mistake is a security hole. Borrowed code is recorded in `docs/sources.md`. The owner's guide for the first PoC: do not make the start complicated.

How users sign in (chosen by the owner on 2026-11-23): a user name and a password. After sign-in the backend gives the browser a signed token, and the browser sends it with every request. Its job in the first PoC is to stand in for single sign-on, so that several users can be told apart. It is kept to the least: a small script creates the users, and there is no page to register, no password reset and no email. Later, single sign-on replaces only the part that issues the token.

The database (chosen by the owner on 2026-11-23): SQLite, with SQL written by hand and no library that maps classes to tables. It holds two small tables: the users, and which user owns which conversation. The owner knows SQL well and has used SQLite. It fits one machine only.

The model (chosen by the owner on 2026-11-23): Claude Haiku 5.5 is the default. The name is a setting and is not written into the code. The reason: the first PoC tests whether the platform works, not how good the answers are. The trial runs used a different model, so the first call to the real model also checks that this one works.

The model's reasoning in the interface (the owner's wish, 2026-11-23): shown, in a block that the user can open. It is the last building task, and it is dropped if it proves troublesome. Three things are known. In the one real run the reasoning arrived together with the answer, so it may not fill the wait. Many answers come with no reasoning. The reasoning can repeat parts of the system prompt. A check on the stored files showed that the SDK returns the stored reasoning summary with the history.

Where requests are processed (the owner agreed on 2026-11-23): the first PoC leaves the provider's default, because it sends test content only. See "Later".

### Plan

The main agent proposed this plan on 2026-11-23. It waits for the owner's approval.

How the tasks are done:

- One task at a time, in the order below. Each task is its own branch and its own pull request.
- `implementer` writes the code. `reviewer` reviews it. The main agent checks the result and explains it to the owner in Chinese.
- The tests use a local stand-in for the model provider, so the automatic checks need no model key. Only task 8 calls a real model.
- Every setting comes from configuration: the model name, the provider's address, the name of the key variable, the storage directory, the database file and the token settings.

The tasks:

- [ ] 1. Skeleton and automatic checks. The owner approved this as the first task on 2026-11-23. A `backend` folder with an empty FastAPI application. A `frontend` folder made with `create-vite`. Linters, type checks and tests for both. The checks run on every pull request. A hook runs them before a session ends. A check that every path in the document map exists. A setup script for the cloud environment that installs the dependencies.
  - Accepted when: one command runs every check; the same checks run on a pull request and pass; a test that fails on purpose makes them fail, shown once; the document map check lets a path be missing only if the map marks it "created at first use"; the check commands are written into `AGENTS.md`. Approval of this plan covers that one edit of `AGENTS.md`.
- [ ] 2. Database and users. A SQLite file with two tables: the users, and the conversations with their owner. SQL written by hand. A script that creates users.
  - Accepted when: tests show that the tables are made on first start and that the script creates a user; no password is stored in a form that can be read back.
- [ ] 3. Sign-in. An endpoint takes a user name and a password and returns a signed token. Every other endpoint needs a valid token. The code follows the official FastAPI full-stack template, and what is borrowed is recorded in `docs/sources.md`.
  - Accepted when: tests show that a wrong password is refused; a request with no token, a changed token or an expired token is refused; a valid token names the right user.
- [ ] 4. The module that touches the SDK. It is the only place that imports the SDK. It starts the runtime inside the backend's process in `empty` mode, with an explicit storage directory, no tools and the project's own system prompt. It gives the rest of the backend three actions: start a conversation, send a message and get the answer in pieces, and read a conversation's history. The SDK has no lock, so the module lets only one message at a time into a conversation. The task also finds out whether the SDK can stop an answer that is being written.
  - Accepted when: tests against the stand-in show that the pieces arrive in order; a conversation can be continued after the backend restarts; a second message to a conversation that is still answering is refused with a clear error; an automatic check fails if any other module imports the SDK.
- [ ] 5. Conversations. Endpoints to start a conversation, to list the user's own conversations and to read one conversation's history. The ownership table is checked before every action.
  - Accepted when: tests show that the list holds only the user's own conversations; reading another user's conversation is refused, and the refusal does not tell whether that conversation exists.
- [ ] 6. Chat with streaming. An endpoint takes a message for a conversation and answers with Server-Sent Events in the project's own message format. The format has three kinds of message: a piece of text, the end, and an error.
  - Accepted when: tests against the stand-in show that the pieces arrive as separate messages in order and that the stream ends with the end message; an error from the provider reaches the browser as an error message and the stream closes; a message to another user's conversation is refused; the generated API documentation describes the endpoints and the message format.
- [ ] 7. Frontend. A sign-in page. A list of the user's conversations with a button for a new one. A chat view that shows the history, sends a message, shows the answer as it arrives, shows its formatting with `react-markdown`, shows that the model is working while nothing has arrived, shows errors, and has a stop button. The code that talks to the backend is one module.
  - Accepted when: unit tests cover the module that reads the stream; one browser test runs the whole path against the backend with the stand-in. In that test user A signs in, starts a conversation, sends a message and sees the answer arrive in pieces. After a reload the history is shown. Then user B signs in and does not see A's conversation.
- [ ] 8. Trial with the real model. One run in the browser with the model from configuration, in a session on the project environment. The trial note records which request settings the runtime chooses for this model, the timing and the token counts. The task also finds out whether the application can change the thinking, effort and output limit settings.
  - Accepted when: a chat turn works from the browser to the real model and back; the findings are in the trial note; the key is in no file and no output.
- [ ] 9. Show the model's reasoning. A fourth kind of message carries pieces of the reasoning summary. The chat view shows them in a block that the user can open and close. The history shows the stored summary too. This task is dropped if it proves troublesome.
  - Accepted when: with a stand-in that sends reasoning, the block shows the pieces and closes when the answer starts; with no reasoning there is no block; an old conversation shows its stored reasoning; a frontend that ignores the new kind of message still works.
- [ ] 10. The owner reads the changes of the first PoC and asks about anything unclear.
- [ ] At the end of the first PoC, look back at the choice of the Copilot SDK with what was learned. Write decision record 0007 if the choice stays and has become costly to change
- [ ] At the end of the first PoC, look back at the working rules. Prune `AGENTS.md` and `CLAUDE.md`. Ask whether the owner's reasons for choices and the owner's reading of changes are enough to find gaps in understanding. Ask whether two untested rules work: "a lesson becomes a check or a rule" and "no new documents outside the document map"

### Not in the first PoC

Tools, knowledge sources and the response cache. Single sign-on. Deployment, and more than one backend machine. A page to register, and password reset. Renaming, deleting and searching conversations. Uploading files. Limits on how much a user may send. Encryption of the session files. A layout for phones.

## Later

Response cache, knowledge sources, connections to databases and other APIs, deployment. Not scheduled yet.

Before a build for hundreds of users, look again at three choices of the first PoC (the owner asked about this on 2026-11-23). Where the runtime runs: inside the backend's process, a crash stops every conversation. Where the conversation history lives: with several backend machines, session files on one machine's disk cannot be read by the others. The database: SQLite fits one machine only, so a database server is needed. The choices of the Copilot SDK and of Server-Sent Events are expected to carry over. Also decide then where requests are processed: the provider's default lets a request be processed in any region, and a setting keeps it in the United States at 1.1 times the price. Whether that setting can be passed through the Copilot SDK is not checked.

Each team may later have its own frontend (the owner's hope, 2026-11-23). Two ways to get there, not chosen yet: one shared frontend with settings for each team, or separate frontends that each team builds on the shared backend API, perhaps with shared components.
