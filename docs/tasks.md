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
- [x] Trial run with a real model provider: one chat turn, once the owner has chosen the provider and supplied a key through the secure form. Done on 2026-11-23 with one difference from this wording: the key was given as the environment variable `POC_MODEL_API_KEY`, not through a form, because a form cannot carry this kind of key (see `docs/status.md`). The run used Anthropic, the model `claude-opus-5-5`, and two chat turns with a disconnect and a resume between them. The provider's data terms were checked first. Notes: the section "Third run: a real model provider" in `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`
- [x] Create the cloud environment `AI-Articheture-Research` for this project only (2026-11-23). The plan was to enter the model key there. For the trial the key was set on the owner's Default environment instead; see `docs/status.md`
- [ ] Write the plan and acceptance criteria for the first PoC, for the owner to review

## First PoC

Goal: a simple frontend and backend; chat with a model through an API key; several users; several conversations per user. The plan is written at the end of the technical research.

First task (approved by the owner on 2026-11-23): set up the automatic checks together with the scaffolding, before any feature code. This covers linters, type checks, tests, CI on pull requests, a hook that runs the checks before a session ends, and a check that every path in the document map exists.

- [ ] At the end of the first PoC, look back at the working rules. Prune `AGENTS.md` and `CLAUDE.md`. Ask whether the owner's reasons for choices and the owner's reading of changes are enough to find gaps in understanding. Ask whether two untested rules work: "a lesson becomes a check or a rule" and "no new documents outside the document map"

## Later

Response cache, knowledge sources, connections to databases and other APIs, deployment. Not scheduled yet.
