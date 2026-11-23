# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- The project has three stages so far: setting the rules (done), the technical research (nearly done), and the first PoC (not started). Use these plain names with the owner. The owner did not agree to short labels for stages and does not want them.
- Setting the rules: done. Both subagent limit tests are done. The concurrent limit of three is enforced. A subagent has no tool for starting another subagent.
- Technical research: finished and checked. Three research notes and one trial note are in `docs/research/research_notes/第一版 PoC 技术调研/`. The report is `docs/research/reports/第一版 PoC 技术调研.md`. Section 12 of the report holds the trial results.
- What the research and the trials found, in short:
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
  - No made-up abbreviations or short labels. The rule is in `AGENTS.md` under "Language".
  - The main agent may merge a pull request that changes only records. The owner still merges rule files, `README.md`, decision records and code. The rule is in `AGENTS.md` under "Branches and merging".
- The agent layer (choice (a) in section 10 of the report): the owner leans to using the SDK and wanted a trial first. The trials without a key passed. No decision record is written yet.
- Cloud environment: a personal environment named `AI-Articheture-Research` was created on 2026-11-23 for this project only. Its network allows `github.com`, `release-assets.githubusercontent.com`, `api.anthropic.com` and the package registries. It has no variables and no setup script yet. The session that created it ran on the owner's Default environment.
- Model key: the owner will use a Claude API key. The owner deleted the first key and will create a new one when it is needed, so that no copy is kept anywhere else. In a cloud session a Claude API key can only be given as an environment variable in the environment's settings. The owner enters it there. It is stored in plain text, every command in a session on that environment can read it, and only a session started afterwards sees it.

## Next step

1. Trial with a real model. The owner creates a new Claude API key and enters it in the settings of the environment `AI-Articheture-Research` as the variable `POC_MODEL_API_KEY`. Do not use the name `ANTHROPIC_API_KEY`: the session's own program may read that name. Then, in a session on that environment, run the trial script from the trial note with provider type `anthropic`, the key read from the variable, and the system prompt replaced. Never print the key. Before the run, check the provider's data terms: how long requests are kept, whether they are used for training, where they are processed.
2. Write decision record 0007 on the agent layer, with the owner's reason in one sentence.
3. Take the owner through choices (b) to (f) in section 10 of the report, one or two at a time, with options, costs and a recommendation.
4. Correct the sentence about the runtime in `README.md`.
5. Write the plan and acceptance criteria for the first PoC in `docs/tasks.md` for the owner to review.

## How to run and verify

There is no project code yet. The trial script is printed at the end of `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`.

## Open items

- Two tasks under "Set the rules" wait for the owner: set the default branch to `main`, and protect `main`. They do not block the first PoC.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription. The vendor advises one GitHub token per user, not a shared one.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
- The new environment has no setup script. When the first PoC has its dependency files, add a setup script that installs them.
