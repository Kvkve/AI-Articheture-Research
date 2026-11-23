# Task list

Marks: `[ ]` not started, `[~]` in progress, `[x]` done.

## M0 Set the rules

- [x] Research workflows and repository conventions for AI-assisted development
- [x] Write the project rules, document structure, agent roles and decisions 0001 to 0005
- [x] Write the project background in `README.md`
- [x] Owner reads the English files
- [ ] Owner sets the default branch to `main` on GitHub
- [ ] Owner protects `main` on GitHub: changes only through a pull request
- [ ] Owner's self-test for M0: explain the branch and pull request flow in their own words, and make one small change alone (tick the two boxes above through a pull request)
- [x] Check that the limits in `.claude/settings.json` are loaded in a new session (both variables are present)
- [x] Test that the concurrent limit is enforced: on 2026-11-23, with the owner's approval, four trivial subagents were started at once. Three ran at the same time and the fourth was refused with "Concurrent subagent limit reached"
- [x] Test that nesting is off: on 2026-11-23, with the owner's approval, a `general-purpose` subagent was asked to start another. It reported that its tool list has no tool for starting subagents, so it could not even try. The outcome is "tool absent", not "call refused". The test does not show whether the setting or the tool's default removes it

## M1 Technical research

Plan (approved by the owner on 2026-11-23): three `researcher` subagents on Sonnet in parallel, then one report written by a subagent on Opus.

- [x] Researcher 1, GitHub Copilot SDK basics: setup with your own model API key, the Python API, streaming output, current limits and preview status. Notes: `docs/research/research_notes/M1 技术调研/copilot_sdk_basics.md`
- [x] Researcher 2, GitHub Copilot SDK for several users: session persistence and resume, isolation between users, deployment shapes (one runtime per user or a shared one). Notes: `docs/research/research_notes/M1 技术调研/copilot_sdk_multi_user.md`
- [x] Researcher 3, open-source components to borrow: frontend and backend scaffolding, chat interface components, conventions for streaming between backend and frontend; the license and maintenance state of each. Notes: `docs/research/research_notes/M1 技术调研/open_source_components.md`
- [x] One report in Chinese for the owner, with sources: `docs/research/reports/M1 技术调研.md`
- [ ] First concept lesson for the owner, built on the report and starting from the data model: what an API is, what a session is, what streaming is
- [ ] Write the M2 plan and acceptance criteria, for the owner to review

## M2 First PoC

Goal: a simple frontend and backend; chat with a model through an API key; several users; several conversations per user. The plan is written at the end of M1.

First task (approved by the owner on 2026-11-23): set up the automatic checks together with the scaffolding, before any feature code. This covers linters, type checks, tests, CI on pull requests, a hook that runs the checks before a session ends, and a check that every path in the document map exists.

## Later

Response cache, knowledge sources, connections to databases and other APIs, deployment. Not scheduled yet.
