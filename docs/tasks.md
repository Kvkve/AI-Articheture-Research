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
- [ ] At the start of the next session, verify that the limits in `.claude/settings.json` work: no more than 3 subagents at once, and a subagent cannot start a subagent

## M1 Technical research

Plan (proposed, needs the owner's go): three `researcher` subagents on Sonnet in parallel, then one report written by a subagent on Opus.

- [ ] Researcher 1, GitHub Copilot SDK basics: setup with your own model API key, the Python API, streaming output, current limits and preview status
- [ ] Researcher 2, GitHub Copilot SDK for several users: session persistence and resume, isolation between users, deployment shapes (one runtime per user or a shared one)
- [ ] Researcher 3, open-source components to borrow: frontend and backend scaffolding, chat interface components, conventions for streaming between backend and frontend; the license and maintenance state of each
- [ ] One report in Chinese for the owner, with sources
- [ ] First concept lesson for the owner, built on the report and starting from the data model: what an API is, what a session is, what streaming is
- [ ] Write the M2 plan and acceptance criteria, for the owner to review

## M2 First PoC

Goal: a simple frontend and backend; chat with a model through an API key; several users; several conversations per user. The plan is written at the end of M1.

Proposed first task: set up the automatic checks together with the scaffolding, before any feature code. This covers linters, type checks, tests, CI on pull requests, a hook that runs the checks before a session ends, and a check that every path in the document map exists.

## Later

Response cache, knowledge sources, connections to databases and other APIs, deployment. Not scheduled yet.
