# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- M0: the rules are set. Both subagent limit tests are done. The concurrent limit of three is enforced. A subagent has no tool for starting another subagent.
- M1 research is finished and checked. Three research notes and one trial note are in `docs/research/research_notes/M1 技术调研/`. The report is `docs/research/reports/M1 技术调研.md`. Section 12 of the report holds the trial results.
- What the research and the trial found, in short:
  - The planned agent SDK is being renamed from GitHub Copilot SDK to Microsoft Copilot SDK. Version 2 (2026-11-18) no longer needs the Copilot CLI program. Its runtime is a separate binary from the same vendor. The Python package downloads it from the release packages of the Copilot CLI repository and loads it inside the application's own process by default.
  - Trial, 2026-11-23: with no GitHub sign-in and a local stand-in for the model provider, the SDK started, streamed an answer, stored the conversation on disk, resumed it, and read the history back with `get_events()`. No outside host was contacted during the run. No real model has been called yet.
  - The runtime adds its own system prompt of about 7,000 characters to every request. It describes a coding agent named GitHub Copilot. A second trial showed that `system_message` with mode "replace" swaps it for the application's own text in full.
  - `mode="empty"`, which the vendor advises for shared use, demands an explicit storage directory and an explicit tool list for each session.
  - The SDK has no notion of a user. The application must keep its own table of which user owns which conversation and check it before every action.
  - No page gives a price for the SDK or the runtime. The runtime bundle has no license file for the runtime itself.
  - The SDK changes fast. Versions must be pinned.
- The working rules changed on 2026-11-23 at the owner's request:
  - Teaching: no prediction questions, explain-back questions or practice exercises. The owner learns through real work, and the focus is the overall design and the key decisions. The rules are in `CLAUDE.md` under "Teaching".
  - Decision records are only for product design choices that are costly to change. There is no decision record yet. The next number is 0007.
- Choice (a), the agent layer: the owner leans to using the SDK and wanted a trial first. The first half of the trial passed. No decision record is written yet.
- Model provider: the owner created a Claude API key with a credit of 100 US dollars. The SDK lists Anthropic as a provider type. The key is not in any cloud environment yet. In a cloud session a Claude API key can only be given as an environment variable in the environment's settings: it cannot be stored as a protected network secret, it is readable by every command in every session that uses the environment, and only a new session picks it up. The session's environment is the owner's Default one, shared by all the owner's projects. The owner was asked how to proceed.
- The owner does not want a pull request yet. All work of this session is on the branch `claude/gallant-brown-mm3dcs` and not on `main`.

## Next step

1. Get the owner's choice of model provider. Then check that provider's data terms: how long requests are kept, whether they are used for training, where they are processed.
2. Second half of the trial: one chat turn against the real provider, with provider type `anthropic`. The owner enters the key in the environment's settings, never in the conversation. The agent's advice was to do this at the start of M2 in an environment made for this project, not in the Default one.
3. Write decision record 0007 on the agent layer, with the owner's reason in one sentence.
4. Take the owner through choices (b) to (f) in section 10 of the report, one or two at a time, with options, costs and a recommendation.
5. Correct the sentence about the runtime in `README.md`.
6. Write the M2 plan and acceptance criteria in `docs/tasks.md` for the owner to review.

## How to run and verify

There is no project code yet. The trial script is printed at the end of `docs/research/research_notes/M1 技术调研/sdk_trial_run.md`.

## Open items

- Two M0 items wait for the owner: set the default branch to `main`, and protect `main`. They do not block M2.
- A new session starts from `main`. Until this branch is merged, a new session will not see this session's work unless it is started on this branch.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription. The vendor advises one GitHub token per user, not a shared one.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
