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
- The first concept lesson (API, session, streaming) was given in conversation on 2026-11-23. The owner has not explained it back yet. Nothing is recorded in `docs/learning/` yet.
- The M2 plan is not written. Six design choices wait for the owner. They are listed in section 10 of the report.

## Next step

1. The owner answers the three explain-back questions of the lesson and writes the `CREATE TABLE` statement for the table of conversation ownership. Record the owner's understanding in `docs/learning/`, in Chinese, with the date.
2. The owner makes the six design choices in section 10 of the report. For each, give the options, the cost of each and a recommendation. Record the ones that are costly to change as decision records.
3. Write the M2 plan and acceptance criteria in `docs/tasks.md` for the owner to review.

The three explain-back questions:

1. After a user clicks "send", which stops does the message pass on its way from the browser to the model and back?
2. The SDK already stores the conversation on disk. Why does the application still need its own table?
3. What is the difference between a streamed and a non-streamed answer? Compare it with something from SQL or Python.

## How to run and verify

There is no code yet.

## Open items

- Three M0 items wait for the owner: set the default branch to `main`, protect `main`, and do the M0 self-test. They do not block M2.
- `README.md` says the SDK "drives the Copilot CLI as its runtime". This is out of date. Correct it when the owner has chosen the agent layer (choice (a) in the report).
- The research did not compare the SDK with other agent SDKs or with a plain model client. If the owner wants that comparison before choosing, it is a new research task.
- Whether using only a model API key works without a GitHub account can only be settled by running the vendor's example. Do this at the start of M2.
