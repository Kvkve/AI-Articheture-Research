# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- The workflow research is finished. The report is `docs/research/reports/AI 协作开发工作流调研.md`.
- The project rules, document structure, agent roles and project background are written and in English.
- Decisions 0001 to 0004 are accepted. Decision 0005 (branching and merging) is proposed and waits for the owner.
- The `main` branch exists.

## Next step

1. The owner reads the English files and says which lines to change.
2. The owner decides on 0005: who merges a branch into `main`.
3. Then the technical research in milestone M1 starts.

## How to run and verify

There is no code yet.

## Open items

- On GitHub the default branch is still the working branch. The owner can change it to `main` under Settings, General, Default branch.
- The subagent limits in `.claude/settings.json` take effect when a new session starts. They are not verified yet. See the task in `docs/tasks.md`.
