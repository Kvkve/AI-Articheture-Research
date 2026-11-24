# Project rules

A personal research project. It studies and tests the architecture of an AI agent platform. It produces a working proof of concept (PoC) and research notes with sources. The owner is not a professional developer: "the owner understands it" is a goal equal to "the feature works".

These rules apply to every AI tool. The project's purpose, target architecture and scope are in `README.md`. Dates and times use US Eastern Time.

## Hard limits

- **No company content.** No real company names, internal system names, repository names, data or screenshots.
- **Cite sources.** Give the link and access date for anything quoted. Mark unverified claims "unverified". Check the license before borrowing code: MIT, Apache-2.0 and BSD are fine; ask the owner about any other. Record borrowed code in `docs/sources.md`.
- **One writer at a time.** Only one party changes code at any moment: the owner, the main agent, or one subagent.
- **Do not change the checks to pass the checks.** Do not edit or delete tests, check configuration or acceptance criteria to get a pass. If you cannot pass honestly, stop and explain.
- **No new documents outside the document map.** Ask the owner before adding a new kind of document.
- **Do not say "done" without verifying.**

## Ask before deciding

- Ask the owner first, and do not choose yourself, when:
  - an instruction can be read in more than one way and the readings lead to different work;
  - something the owner did not mention would change what gets built;
  - a design or technology choice has more than one workable option;
  - an action is hard to undo.
- Small details inside an approved plan that have a common default can be done directly. List the assumptions you made when you report.
- When you ask, give the options, the cost of each, and a recommendation.
- A subagent cannot ask the owner. In the cases above it stops and reports to the main agent.

## What needs the owner's approval

Design decisions, milestone plans, changes to this file and to `CLAUDE.md`, and actions that cannot be undone, such as deleting data or rewriting git history. Work inside an approved plan does not need item-by-item approval.

## Branches and merging

- `main` holds approved work. Do not push to `main` directly.
- Do each piece of work on its own branch. When it is ready, open a pull request to `main`.
- A pull request is merged only when the owner agrees. The owner merges it, or tells the main agent in the conversation to merge it.
- One agreement covers one pull request.
- Before asking the owner to agree, the main agent says in Chinese what the pull request changes.
- The main agent does not merge while an automatic check fails.

## Language

Files in this repository are in English. Two kinds are in Chinese: the owner's learning notes in `docs/learning/`, and research reports written for the owner to read. Conversation with the owner is in Chinese. Explain each rule or decision to the owner in Chinese before asking for approval. Write English in short sentences with common words. Do not make up abbreviations or short labels for stages, tasks or parts of the system. Use plain names.

## Document map

| When | Read | What it holds |
|---|---|---|
| Starting a session | `docs/status.md` | Where the work stands, the next step, how to run and verify |
| Choosing what to do next | `docs/tasks.md` | Milestones and the task list |
| You need the purpose, target architecture or scope | `README.md` | Project background |
| You need to know what is built now and where its code is | `docs/architecture.md` | Diagrams of the parts that exist and of how a request travels; a table of where the code of each part is |
| Making or changing a design choice | `docs/decisions/README.md` | Index of decisions; each decision is a file in the same folder |
| You need evidence or want to cite something | `docs/research/reports/` | Research reports; raw notes are in `docs/research/research_notes/` |
| Borrowing outside code | `docs/sources.md` | Third-party sources and licenses |
| Explaining to the owner or reviewing a lesson | `docs/learning/` | The owner's learning notes (created at first use) |

## Keeping documents in order

- Rewrite `docs/status.md` in full at the end of each session. Do not append. Git keeps the history.
- Prune this file and `CLAUDE.md` at the end of each milestone. Rule files grow over time.
- Decision records:
  - Write one only for a choice about the design of the product that has real alternatives and would be costly to change later. Small choices do not get one. Rules about how the work is done are not decisions: change the rule in this file or in `CLAUDE.md`, and give the reason in the commit message.
  - One decision per file, numbered in order. Update the index in `docs/decisions/README.md` in the same change.
  - Status is one of three. "Proposed" is for reference only. "Accepted" must be followed. "Superseded" is history only. Only the owner can make a decision "Accepted".
  - A new decision that changes an old one marks the old one "Superseded" in the same change. Each links to the other.
  - If a task conflicts with an accepted decision, or two accepted decisions conflict, stop and ask. Do not pick one.
  - The owner can change any decision at any time. Record the change as a new decision and list the finished work it affects.
  - Review all accepted decisions at the end of each milestone.
- Lessons do not get their own file. Turn a lesson into an automatic check, a line in this file, or an edit to an existing document. If none fits, do not record it.
- `docs/learning/` records the owner's understanding, with dates. It is not a set of rules.

## Code conventions

- Comments say why, not what the code does.
- No hard-coded configuration values (addresses, keys, model names, limits). Read them from configuration.
- No placeholder implementations and no TODOs. If something cannot be finished, record it in `docs/tasks.md` and say so.

Check commands:

- `./scripts/setup.sh` installs the dependencies of the backend and the frontend from their lock files.
- `./scripts/check.sh` runs every check and stops at the first failure. It checks the document map, then the Python code in `backend/` and `scripts/` (ruff, mypy, pytest), then the code in `frontend/` (ESLint, the TypeScript compiler, Vitest).
- The same command runs on every pull request, and before the main agent ends a turn in Claude Code.

The rules for each language are in the tool settings: `backend/pyproject.toml` for Python, and `frontend/eslint.config.js` with the `tsconfig` files for TypeScript.

## Definition of done

A task is done when all three hold: it meets the acceptance criteria written for it in `docs/tasks.md`; all automatic checks pass; a party that did not write it has reviewed it.

A milestone is done when, in addition, the owner has read its changes and every question the owner asked about them has been answered.
