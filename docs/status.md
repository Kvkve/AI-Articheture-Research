# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- The workflow research is finished. The report is `docs/research/reports/AI 协作开发工作流调研.md`.
- The project rules, document structure, agent roles and project background are written. The owner has read them.
- Decisions 0001 to 0005 are accepted.
- `main` exists. Work reaches it through pull requests that the owner merges.
- The owner approved the M1 plan and the first task of M2 by merging pull request 1.

## Next step

Start milestone M1 in a new session, following the plan in `docs/tasks.md`. Before starting the researchers, run the two limit tests listed under M0 in `docs/tasks.md`. One of them starts four subagents, so ask the owner first.

## How to run and verify

There is no code yet.

## Open items

- Three M0 items wait for the owner: set the default branch to `main`, protect `main`, and do the M0 self-test. They do not block M1.
- The subagent limits are loaded: both variables from `.claude/settings.json` are present in a session started after the file was added. Whether they are enforced is not tested yet.
