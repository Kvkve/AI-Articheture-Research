# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- M0: the rules are set. Both subagent limit tests are done. The concurrent limit of three is enforced. A subagent has no tool for starting another subagent.
- M1 research is finished and checked. Three notes are in `docs/research/research_notes/M1 技术调研/`. The report is `docs/research/reports/M1 技术调研.md`. The main agent fetched 15 of the cited sources again and recorded the result at the end of each note.
- What the research found, in short:
  - The planned agent SDK is being renamed from GitHub Copilot SDK to Microsoft Copilot SDK. Version 2 (2026-11-18) no longer needs the Copilot CLI. Its runtime is a separate component from the same vendor. The Python package downloads it and loads it inside the application's own process by default.
  - Using only the project's own model API key needs no Copilot subscription and no GitHub sign-in, by the vendor's documents. No one has confirmed this by a run yet. The license of the runtime itself, and whether it sends data to the vendor, are not stated on the official pages read.
  - The SDK keeps each conversation as a folder of files on the disk of the machine that runs the runtime. It has no notion of a user. The application must keep its own table of which user owns which conversation and check it before every action.
  - The SDK changes fast. Versions must be pinned.
- Decision 0006 is accepted and replaces 0003. The owner learns through real work: the owner makes each design choice with a one-sentence reason and reads each change before merging. There are no prediction questions, explain-back questions or practice exercises. The owner's focus is the overall design and the key decisions, not every detail.
- The first concept lesson (API, session, streaming) was given in conversation. The owner's follow-up questions were answered.
- The M2 plan is not written. Six design choices wait for the owner. They are in section 10 of the report. Choice (a), the agent layer, was put to the owner on 2026-11-23 with a recommendation. It is not answered yet.

## Next step

1. Get the owner's answer on choice (a): use the SDK from the first PoC, start with a plain model client, or research other agent SDKs first. The agent recommended the SDK, with a trial run of the vendor's example as the first step of M2. The trial needs a model API key, so ask which model provider the owner will use.
2. Take the owner through choices (b) to (f), one or two at a time. For each, give the options, the cost of each and a recommendation. The owner gives the reason in one sentence. Record the ones that are costly to change as decision records.
3. Correct the sentence about the runtime in `README.md` once choice (a) is made.
4. Write the M2 plan and acceptance criteria in `docs/tasks.md` for the owner to review.

## How to run and verify

There is no code yet.

## Open items

- Two M0 items wait for the owner: set the default branch to `main`, and protect `main`. They do not block M2.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The vendor says that using only a model API key needs no GitHub sign-in. Confirm it by running the vendor's example. During that run, also note which outside hosts the runtime contacts.
- Look back at decision 0006 at the end of M2: are the owner's reasons for choices and the reading of changes enough to find gaps in understanding?
