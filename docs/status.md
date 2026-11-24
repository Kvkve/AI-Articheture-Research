# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- The project has three stages so far: setting the rules (done), the technical research (done except for the plan of the first PoC), and the first PoC (not started). Use these plain names with the owner. The owner did not agree to short labels for stages and does not want them.
- Setting the rules: done. Both subagent limit tests are done. The concurrent limit of three is enforced. A subagent has no tool for starting another subagent.
- Technical research: finished and checked. Three research notes and one trial note are in `docs/research/research_notes/第一版 PoC 技术调研/`. The report is `docs/research/reports/第一版 PoC 技术调研.md`. Section 12 of the report holds the trial results.
- What the research and the trials found, in short:
  - The planned agent SDK is being renamed from GitHub Copilot SDK to Microsoft Copilot SDK. Version 2 (2026-11-18) no longer needs the Copilot CLI program. Its runtime is a separate binary from the same vendor. The Python package downloads it from the release packages of the Copilot CLI repository and loads it inside the application's own process by default.
  - Trials without a key, 2026-11-23: with no GitHub sign-in and a local stand-in for the model provider, the SDK started, streamed an answer, stored the conversation on disk, resumed it, and read the history back with `get_events()`.
  - Trial with a real model, 2026-11-23: the same flow worked against Anthropic with the model `claude-opus-5-5`. Two turns, with a disconnect and a resume between them. After the resume the model still knew the first turn. Apart from one DNS lookup, the only outside connection was to the provider. No GitHub sign-in was needed. The run cost about $0.004.
  - The runtime adds its own system prompt of about 7,000 characters to every request. It describes a coding agent named GitHub Copilot. `system_message` with mode "replace" swaps it for the application's own text in full. The real run confirmed this.
  - With a real model the runtime chooses several request settings by itself: thinking on, effort "medium", an output limit of 48,000 tokens, and prompt-cache markers. Whether the application can change them is not tested.
  - In the real run the first answer arrived all at once after 3 seconds, although streaming was on. The model's thinking came first. The second answer started after 0.6 seconds.
  - The real model sends reasoning events with a summary of its thinking. The stored conversation file keeps that summary as plain text, next to the messages.
  - Under BYOK the SDK reports a cost of 0. The application must work out cost from the token counts.
  - `mode="empty"`, which the vendor advises for shared use, demands an explicit storage directory and an explicit tool list for each session.
  - The SDK has no notion of a user. The application must keep its own table of which user owns which conversation and check it before every action.
  - No page gives a price for the SDK or the runtime. The runtime bundle has no license file for the runtime itself.
  - The SDK changes fast. Versions must be pinned.
- The provider's data terms, read 2026-11-23: API requests are deleted within 30 days, and flagged ones can be kept for up to 2 years; the commercial terms forbid training on customer content; by default a request may be processed in any region, and a setting keeps it in the United States at 1.1 times the price. Sources are in the trial note.
- The working rules changed on 2026-11-23 at the owner's request:
  - Teaching: no prediction questions, explain-back questions or practice exercises. The owner learns through real work, and the focus is the overall design and the key decisions. The rules are in `CLAUDE.md` under "Teaching".
  - Decision records are only for product design choices that are costly to change. There is no decision record yet. The next number is 0007.
  - No made-up abbreviations or short labels. The rule is in `AGENTS.md` under "Language".
  - Merging: a pull request is merged only when the owner agrees. The owner may tell the main agent in the conversation to merge it. The main agent first says in Chinese what the pull request changes. The rule is in `AGENTS.md` under "Branches and merging".
- The agent layer (choice (a) in section 10 of the report): the owner decided on 2026-11-23 that the first PoC uses the Copilot SDK. The reasons and the conditions are in `docs/tasks.md` under "First PoC". The SDK was not compared with other options. No decision record is written, because the choice is cheap to change in a first PoC. The choice is looked at again at the end of the first PoC.
- Where the runtime runs (choice (b)): the owner decided on 2026-11-23 that it runs inside the backend's own process. The reason and the accepted cost are in `docs/tasks.md` under "First PoC".
- Where the conversation history lives (choice (c)): the owner decided on 2026-11-23 that it lives only in the SDK's session files. The application keeps its own table of which user owns which conversation. The reason and the accepted cost are in `docs/tasks.md` under "First PoC".
- How answers travel from the backend to the browser (the first half of choice (d)): the owner decided on 2026-11-23 to use Server-Sent Events. The message format, the second half, is chosen together with the frontend in choice (e).
- The frontend (choice (e)) and the message format (the second half of choice (d)): the owner decided on 2026-11-23 on hand-written React components and the project's own small message format. The owner hopes that each team can later have its own frontend, so the backend API and the message format are treated as a contract. The details are in `docs/tasks.md` under "First PoC" and "Later".
- Where the project skeleton comes from (choice (f)): the owner decided on 2026-11-23 on a small start. `create-vite` makes the frontend skeleton, the backend is hand-written, and the sign-in part follows the official FastAPI template. The owner's guide: do not make the start complicated. All six choices of section 10 of the report are now made.
- The owner expects the final platform to serve hundreds of users at once. Two choices of the first PoC do not carry over to that size: where the runtime runs, and where the history lives. `docs/tasks.md` lists this under "Later".
- Model key: the project environment `AI-Articheture-Research` holds a Claude API key as the variable `POC_MODEL_API_KEY`. The owner entered it there on 2026-11-23. Before that, for the real trial, the key was on the owner's Default environment. The trial never printed it and wrote it to no file. After the trial the variable was removed from Default at the owner's word.
- How a key is given: in a cloud session a Claude API key can only be given as an environment variable in the environment's settings, not through the secure form. A variable is stored in plain text, and every session on that environment can read it. Only a session started afterwards sees it.
- Cloud environments: the project environment `AI-Articheture-Research` (created 2026-11-23) allows `github.com`, `release-assets.githubusercontent.com`, `api.anthropic.com` and the package registries. It has one variable, `POC_MODEL_API_KEY`, and no setup script. The session that ran the real trial ran on Default, which has unrestricted network access.

## Next step

1. Ask the owner about the points that the choices left open, with options, costs and a recommendation: how users sign in; which database; which model the product uses; whether the interface shows the model's reasoning; whether requests should be kept in the United States. Where the research did not compare options, say so, and do not ask the owner to justify a choice the research gave no material for.
2. Write the plan and acceptance criteria for the first PoC in `docs/tasks.md` for the owner to review.
3. When work needs to call the model, start a new session on the project environment `AI-Articheture-Research`. A session uses the environment chosen when it starts, so a session on Default cannot read the key. Where to choose it: on the screen for starting a new session, the environment selector is the first control in the row under the message box. It lists every environment, with a settings icon on each row. It is shown only until the first message of the new session is sent. The menu at the title of a running session only edits that session's own environment. Source: [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments), read 2026-11-23. The owner has found the selector. Work that does not call the model can run on any environment.

## How to run and verify

There is no project code yet. The trial scripts are printed at the end of `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`. The script of the third run reads the provider address, the model name and the name of the key variable from the environment. Never print the key. Do not name the key variable `ANTHROPIC_API_KEY`: the session's own program may read that name.

For trial runs, call a low-cost model, not Opus. The owner said so on 2026-11-23 after the real trial used `claude-opus-5-5`. The runtime may choose other request settings for another model, so run one trial with the product's model once the owner has chosen it.

## Open items

- Two tasks under "Set the rules" wait for the owner: set the default branch to `main`, and protect `main`. They do not block the first PoC.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The real trial was one run with one model. Not tested: latency over many runs, long answers, provider errors such as a wrong key or a rate limit, other models, and changing the settings the runtime chooses.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription. The vendor advises one GitHub token per user, not a shared one.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
- The project environment has no setup script. When the first PoC has its dependency files, add a setup script that installs them.
