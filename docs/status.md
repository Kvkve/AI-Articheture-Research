# Current status

Updated 2026-11-23 (US Eastern Time).

## Where the work stands

- The project has three stages so far: setting the rules (done), the technical research (done), and the first PoC (planned, not started). Use these plain names with the owner. The owner did not agree to short labels for stages and does not want them.
- Technical research: finished and checked. Three research notes and one trial note are in `docs/research/research_notes/第一版 PoC 技术调研/`. The report is `docs/research/reports/第一版 PoC 技术调研.md`. Section 12 of the report holds the trial results.
- The first PoC: every design choice is made, and a plan with acceptance criteria is written. Both are in `docs/tasks.md` under "First PoC". The plan was proposed on 2026-11-23 and waits for the owner's approval.
- The choices in one line each. The reasons and the accepted costs are in `docs/tasks.md`.
  - Agent layer: the Copilot SDK. It was not compared with other options. All code that touches it stays in one module.
  - The runtime runs inside the backend's own process.
  - The conversation history lives only in the SDK's session files. The application keeps its own table of which user owns which conversation.
  - Answers travel to the browser by Server-Sent Events, in the project's own small message format.
  - The frontend is hand-written React components. The code that talks to the backend is one module.
  - The skeleton is small: `create-vite` for the frontend, a hand-written FastAPI backend. Sign-in follows the official FastAPI template.
  - Sign-in is a user name and a password with a signed token, kept to the least. It stands in for single sign-on.
  - The database is SQLite, with SQL written by hand.
  - The default model is Claude Haiku 5.5, set in configuration.
  - The interface shows the model's reasoning. This is the last building task and is dropped if it proves troublesome.
  - No decision record is written. The choices are cheap to change in a first PoC. The next number is 0007.
- What the owner wants from the project, said on 2026-11-23:
  - Do not make the start complicated.
  - The final platform may serve hundreds of users at once. Three choices of the first PoC do not carry over to that size: where the runtime runs, where the history lives, and the database. `docs/tasks.md` lists this under "Later".
  - Each team may later have its own frontend. So the backend API and the message format are a contract: written down, and free of anything only one frontend needs.
  - People the owner works with also recommend the Copilot SDK. The owner cannot share their documents. Do not ask for them.
- What the research and the trials found, in short:
  - The agent SDK is being renamed from GitHub Copilot SDK to Microsoft Copilot SDK. Since version 2 (2026-11-18) its runtime is a separate binary from the same vendor. The Python package downloads it and loads it inside the application's own process by default.
  - With no GitHub sign-in, the SDK started, streamed an answer, stored the conversation on disk, resumed it and read the history back with `get_events()`. This held against a local stand-in and against a real model (Anthropic, `claude-opus-5-5`, one run, about $0.004).
  - In the real run, apart from one DNS lookup, the only outside connection was to the provider.
  - The runtime adds its own system prompt of about 7,000 characters. `system_message` with mode "replace" swaps it for the application's own text in full.
  - With a real model the runtime chooses several request settings by itself: thinking on, effort "medium", an output limit of 48,000 tokens, and prompt-cache markers. Whether the application can change them is not tested.
  - In the real run the first answer arrived all at once after 3 seconds, although streaming was on. The reasoning and the answer came together. The second answer started after 0.6 seconds.
  - The real model sends reasoning events with a summary of its thinking. The stored file keeps that summary as plain text, and `get_events()` returns it with the history.
  - Under BYOK the SDK reports a cost of 0. The application must work out cost from the token counts.
  - `mode="empty"`, which the vendor advises for shared use, demands an explicit storage directory and an explicit tool list for each session.
  - The SDK has no notion of a user and no lock. Two requests on one conversation at the same time are undefined.
  - No page gives a price for the SDK or the runtime. The runtime bundle has no license file for the runtime itself.
  - The SDK changes fast. Versions must be pinned.
- The provider's data terms, read 2026-11-23: API requests are deleted within 30 days, and flagged ones can be kept for up to 2 years; the commercial terms forbid training on customer content; by default a request may be processed in any region, and a setting keeps it in the United States at 1.1 times the price. Sources are in the trial note.
- Model key: the project environment `AI-Articheture-Research` holds a Claude API key as the variable `POC_MODEL_API_KEY`. The owner entered it there on 2026-11-23. The Default environment no longer holds it.
- Cloud environments: the project environment allows `github.com`, `release-assets.githubusercontent.com`, `api.anthropic.com` and the package registries. It has one variable and no setup script.

## How the work with the owner goes

These points come from 2026-11-23. The rules themselves are in `AGENTS.md` and `CLAUDE.md`.

- Teaching: no prediction questions, explain-back questions or practice exercises. The owner learns through real work. The focus is the overall design and the key decisions.
- For a choice, give the options, the cost of each and a recommendation, and ask whether the owner agrees. Do not ask the owner to justify a choice the research gave no material for. Say plainly where the research did not compare options.
- Explain a new idea from what the owner knows: SQL, some Java and Python. The owner has used SQLite.
- Merging: a pull request is merged only when the owner agrees. The owner may tell the main agent in the conversation to merge it. The main agent first says in Chinese what the pull request changes.
- Collect small record changes into one pull request. Do not open a pull request for each.
- Trial runs call a low-cost model, not Opus. Review subagents stay on the model in their definition.
- No company content. The owner's workplace has internal documents on this topic. They must not be uploaded or copied into the repository.

## Next step

1. If the plan is not yet approved, ask the owner to approve it. Explain it in Chinese first.
2. Start task 1 of the plan: the skeleton and the automatic checks. Start a new session for it, on the project environment `AI-Articheture-Research`.
3. Then the tasks of the plan in order, one at a time.

How to start a session on the project environment: on the screen for starting a new session, the environment selector is the first control in the row under the message box. It is shown only until the first message is sent. The menu at the title of a running session only edits that session's own environment. Source: [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments), read 2026-11-23. The owner has found the selector. A session uses the environment chosen when it starts, and only a session started after a variable was set can read it.

## How to run and verify

There is no project code yet. Task 1 of the plan adds the check commands.

The trial scripts are printed at the end of `docs/research/research_notes/第一版 PoC 技术调研/sdk_trial_run.md`. The script of the third run reads the provider address, the model name and the name of the key variable from the environment. Never print the key. Do not name the key variable `ANTHROPIC_API_KEY`: the session's own program may read that name. In a cloud session a Claude API key can only be given as an environment variable in the environment's settings, not through the secure form.

## Open items

- Two tasks under "Set the rules" wait for the owner: set the default branch to `main`, and protect `main`. They do not block the first PoC.
- The research did not compare the SDK with other agent SDKs or with a plain model client.
- The real trial was one run with one model, and it was not the model now chosen. Not tested: latency over many runs, long answers, provider errors such as a wrong key or a rate limit, and changing the settings the runtime chooses. Task 8 of the plan covers part of this.
- Whether the SDK can stop an answer that is being written is not checked. Task 4 of the plan finds out.
- Using a Copilot subscription in place of a model key is a documented sign-in method of the SDK. It is not tested, because it needs a subscription.
- The SDK keeps the conversation content as plain files on disk. Whether these files can be encrypted was not found.
