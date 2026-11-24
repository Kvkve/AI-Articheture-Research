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
- [ ] Write the plan and acceptance criteria for the first PoC, for the owner to review

## First PoC

Goal: a simple frontend and backend; chat with a model through an API key; several users; several conversations per user. The plan is written at the end of the technical research.

First task (approved by the owner on 2026-11-23): set up the automatic checks together with the scaffolding, before any feature code. This covers linters, type checks, tests, CI on pull requests, a hook that runs the checks before a session ends, and a check that every path in the document map exists.

Agent layer (chosen by the owner on 2026-11-23): the first PoC uses the Copilot SDK. The reasons: it is the SDK this project set out to study; three trial runs, the last one against a real model, showed that it works with the project's own model key; people the owner works with also recommend it, and the first PoC is meant as a reference for a later build in that setting. It was not compared with other options. All code that touches the SDK stays in one module, so that the SDK can be replaced. No decision record is written now, because the choice is cheap to change in a first PoC.

Where the runtime runs (chosen by the owner on 2026-11-23): inside the backend's own process. This is the SDK's default and the only way the trial runs tested. A crash of the runtime then stops the backend and every conversation in progress. That is accepted for a first PoC on one machine. The connection type is set in the one module that touches the SDK, so it can be changed to a child process later.

Where the conversation history lives (chosen by the owner on 2026-11-23): only in the SDK's session files on the backend's disk. The backend reads the history back through the SDK. The application keeps its own table of which user owns which conversation, and checks it before every action on a conversation. The trial runs tested storing, resuming and reading back. The cost: the content cannot be queried with SQL, and the vendor decides the file format. A copy in the application's own database can be added later in the one module that touches the SDK.

How answers travel from the backend to the browser (chosen by the owner on 2026-11-23): Server-Sent Events. One direction is enough for question-and-answer chat. FastAPI has it built in. The ready-made chat formats that the research found are built on it, so the choice fits a hand-written frontend and a component library alike. What each message holds is chosen together with the frontend. This project has not run any of the transport options yet.

The frontend (chosen by the owner on 2026-11-23): hand-written React components. One small library, `react-markdown`, shows the formatting of answers. The message format over Server-Sent Events is the project's own and stays small. The reasons: every step of the path stays in the project's own code, and there is no second fast-changing dependency next to the SDK. The cost: a plain interface, and the project writes the stop button, the scrolling and the error display itself. The owner hopes that each team can later have its own frontend. So the backend API and the message format are a contract: they are written down, and they hold nothing that only this one frontend needs. In the frontend, the code that talks to the backend stays in one module, apart from the components that draw the page.

- [ ] At the end of the first PoC, look back at the choice of the Copilot SDK with what was learned. Write decision record 0007 if the choice stays and has become costly to change
- [ ] At the end of the first PoC, look back at the working rules. Prune `AGENTS.md` and `CLAUDE.md`. Ask whether the owner's reasons for choices and the owner's reading of changes are enough to find gaps in understanding. Ask whether two untested rules work: "a lesson becomes a check or a rule" and "no new documents outside the document map"

## Later

Response cache, knowledge sources, connections to databases and other APIs, deployment. Not scheduled yet.

Before a build for hundreds of users, look again at two choices of the first PoC (the owner asked about this on 2026-11-23). Where the runtime runs: inside the backend's process, a crash stops every conversation. Where the conversation history lives: with several backend machines, session files on one machine's disk cannot be read by the others. The choices of the Copilot SDK and of Server-Sent Events are expected to carry over.

Each team may later have its own frontend (the owner's hope, 2026-11-23). Two ways to get there, not chosen yet: one shared frontend with settings for each team, or separate frontends that each team builds on the shared backend API, perhaps with shared components.
