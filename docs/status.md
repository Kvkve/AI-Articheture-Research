# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- The workflow research is finished. The report is `docs/research/reports/AI 协作开发工作流调研.md`.
- The project rules, document structure, agent roles and project background are written. The owner has read them.
- Decisions 0001 to 0005 are accepted.
- `main` exists. Work now reaches it through pull requests that the owner merges.

## Next step

1. The owner finishes milestone M0: the items marked for the owner in `docs/tasks.md`.
2. The owner approves or changes the M1 plan in `docs/tasks.md`.
3. M1 starts, preferably in a new session. A new session also tests whether these records are enough to hand the work over.

## How to run and verify

There is no code yet.

## Open items

- The subagent limits in `.claude/settings.json` take effect when a new session starts. They are not verified yet.
- Automatic checks for code (linters, tests, CI, a hook that runs checks before a session ends) are planned as the first task of M2. The owner has not approved that plan yet.
