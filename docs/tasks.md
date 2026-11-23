# Task list

Marks: `[ ]` not started, `[~]` in progress, `[x]` done.

## M0 Set the rules

- [x] Research workflows and repository conventions for AI-assisted development
- [x] Write the project rules, document structure, agent roles and decisions 0001 to 0004
- [x] Write the project background in `README.md`
- [~] Owner reads the English files and asks for changes
- [ ] Owner decides on decision 0005 (branching and merging)
- [ ] At the start of the next session, verify that the limits in `.claude/settings.json` work: no more than 3 subagents at once, and a subagent cannot start a subagent

## M1 Technical research

- [ ] GitHub Copilot SDK official docs and examples: using your own API key, session persistence, isolation between users, streaming output
- [ ] Open-source components to borrow: frontend and backend scaffolding, chat interface components, conventions for streaming; check the license and maintenance state of each
- [ ] Write the M2 plan and acceptance criteria from the research, for the owner to review

## M2 First PoC

Goal: a simple frontend and backend; chat with a model through an API key; several users; several conversations per user. The plan is written at the end of M1.

## Later

Response cache, knowledge sources, connections to databases and other APIs, deployment. Not scheduled yet.
