# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- M0: the rules are set. Both subagent limit tests are done. The concurrent limit of three is enforced. A subagent has no tool for starting another subagent.
- M1 research is finished and checked. Three notes are in `docs/research/research_notes/M1 技术调研/`. The report is `docs/research/reports/M1 技术调研.md`. The main agent had 19 of the cited pages read again and recorded the result at the end of the notes.
- What the research found, in short:
  - The planned agent SDK is being renamed from GitHub Copilot SDK to Microsoft Copilot SDK. Version 2 (2026-11-18) no longer needs the Copilot CLI. Its runtime is a separate component from the same vendor. The Python package downloads it and loads it inside the application's own process by default.
  - Using only the project's own model API key needs no Copilot subscription and no GitHub sign-in, by the vendor's documents. No one has confirmed this by a run yet. No page gives a price for the SDK or the runtime. The license of the runtime itself, and whether it sends data to the vendor, are not stated on the official pages read.
  - The SDK keeps each conversation as a folder of files on the disk of the machine that runs the runtime. It has no notion of a user. The application must keep its own table of which user owns which conversation and check it before every action.
  - The SDK changes fast. Versions must be pinned.
- The working rules changed on 2026-11-23 at the owner's request:
  - Teaching: no prediction questions, explain-back questions or practice exercises. The owner learns through real work, and the focus is the overall design and the key decisions. The rules are in `CLAUDE.md` under "Teaching".
  - Decision records are only for product design choices that are costly to change. The six earlier records held working rules and were removed. There is no decision record yet. The next number is 0007.
- Choice (a), the agent layer: the owner leans to using the SDK in the first PoC and trying it first. No decision record is written yet. Write it after the trial run, with the result.
- The owner asked whether the model provider keeps the requests. The answer given was general and marked unverified. The provider's actual terms must be checked once the provider is chosen.
- The M2 plan is not written. Choices (b) to (f) in section 10 of the report still wait for the owner.

## Next step

1. Find out from the owner which model provider the project will use. It is needed for a real model call and for checking that provider's data terms (how long requests are kept, whether they are used for training, where they are processed).
2. If the owner agrees, do a trial run of the vendor's example. Part 1 needs no key: install the SDK, start the runtime with no GitHub sign-in, and note which outside hosts it contacts. Part 2 needs the key: one chat turn with streaming, then read the history back. Record the result in the basics note and the report. Then write decision record 0007 on the agent layer, with the owner's reason.
3. Take the owner through choices (b) to (f), one or two at a time, with options, costs and a recommendation.
4. Correct the sentence about the runtime in `README.md`.
5. Write the M2 plan and acceptance criteria in `docs/tasks.md` for the owner to review.

## How to run and verify

There is no code yet.

## Open items

- Two M0 items wait for the owner: set the default branch to `main`, and protect `main`. They do not block M2.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The conversation content is kept as plain files on disk by the SDK. Whether these files can be encrypted was not found.
