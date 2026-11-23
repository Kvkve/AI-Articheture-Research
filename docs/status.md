# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- M0: the rules are set. Both subagent limit tests are done. The concurrent limit of three is enforced. A subagent has no tool for starting another subagent.
- M1 research is finished and checked. Three notes are in `docs/research/research_notes/M1 技术调研/`. The report is `docs/research/reports/M1 技术调研.md`. The main agent fetched 15 of the cited sources again and recorded the result at the end of each note.
- What the research found, in short:
  - The planned agent SDK is being renamed from GitHub Copilot SDK to Microsoft Copilot SDK. Version 2 (2026-11-18) no longer needs the Copilot CLI. Its runtime loads inside the application's own process by default.
  - Using only the project's own model API key needs no Copilot subscription, by the vendor's documents. Whether it needs a GitHub account is not verified.
  - The SDK keeps each conversation as a folder of files on the disk of the machine that runs the runtime. It has no notion of a user. The application must keep its own table of which user owns which conversation and check it before every action.
  - The SDK changes fast. Versions must be pinned.
- The first concept lesson (API, session, streaming) was given in conversation on 2026-11-23. The owner asked two follow-up questions, on what replaced the Copilot CLI as the runtime and on where history is stored in the cloud. Both were answered in conversation. Nothing is recorded in `docs/learning/`.
- The M2 plan is not written. Six design choices wait for the owner. They are listed in section 10 of the report.

## Next step

1. The owner said on 2026-11-23 that quiz-style steps are not wanted: no prediction questions, no explain-back questions, no practice exercises. The owner wants to learn and write only for real work or to understand what the agent did. A change to decision 0003, to the "Teaching" rules in `CLAUDE.md` and to the milestone line in "Definition of done" in `AGENTS.md` was proposed in conversation and waits for the owner's answer. Until it is settled, do not ask the owner to predict, explain back or do exercises.
2. The owner makes the six design choices in section 10 of the report. For each, give the options, the cost of each and a recommendation. Record the ones that are costly to change as decision records.
3. Write the M2 plan and acceptance criteria in `docs/tasks.md` for the owner to review.

## How to run and verify

There is no code yet.

## Open items

- Three M0 items wait for the owner: set the default branch to `main`, protect `main`, and do the M0 self-test. They do not block M2.
- `README.md` says the SDK "drives the Copilot CLI as its runtime". This is out of date. Correct it when the owner has chosen the agent layer (choice (a) in the report).
- The research did not compare the SDK with other agent SDKs or with a plain model client. If the owner wants that comparison before choosing, it is a new research task.
- Whether using only a model API key works without a GitHub account can only be settled by running the vendor's example. Do this at the start of M2.
