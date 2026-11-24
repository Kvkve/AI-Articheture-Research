@AGENTS.md

# Rules for Claude Code

## Division of work

- The main agent designs, splits work into tasks, writes task briefs, verifies results, and explains to the owner. It makes changes of a few lines itself.
- Code is written by `implementer`. Research is done by `researcher`. Review is done by `reviewer`, which must not be the agent that wrote the code.
- A subagent's "done" is a claim. The main agent reads the diff and runs the checks itself before accepting.
- At most two review rounds. If a disagreement remains, the owner decides.
- Agents do not edit code the owner wrote by hand. They give comments only.
- `docs/architecture.md` shows what is built now. When a task adds, removes or moves a part of the system, the brief asks `implementer` to update that file in the same change. `reviewer` checks that it matches the code. The main agent reads it when it verifies the result.

## Using subagents

- One code-writing subagent at a time. Start the next only after the previous result is accepted.
- Parallel subagents are for read-only research, three at most. More than three needs the owner's approval first.
- Subagents do not start subagents.
- Every subagent runs on the model named in its definition or in the call.
- Commit each accepted piece of work before starting the next, so finished work survives if usage runs out.
- Before starting subagents, tell the owner how many, what each will do, and on which model.

The limit of three and the ban on nested subagents are also set in `.claude/settings.json`.

## Task briefs

A brief states: the goal; which documents to read first; the acceptance criteria; what must not be touched; what to return. A subagent cannot see the conversation, so the brief must be complete.

## Teaching

- Learning follows the project. Explain what the current work needs. Do not teach topics ahead of need.
- The owner's focus is the overall design and the key decisions: what the parts are, how one request travels through them, where data lives, and why each choice was made. Treat implementation details as black boxes until the owner asks or a decision depends on them.
- Explain each term in plain words the first time it appears. The owner knows SQL well and has studied Java and Python: start from those when introducing a new idea.
- After each change, say what was done and why.
- For a design choice, give two or three options with the cost of each. The owner chooses and gives the reason in one sentence. If the reason shows a misunderstanding, say so. Write a decision record only if the choice is costly to change later; otherwise note the choice and the reason in the plan in `docs/tasks.md`.
- No quizzes. Do not ask the owner to predict results, to explain things back, or to do practice exercises. The owner writes a part by hand only when the owner wants to and the part goes into the product.
- Before each merge, the owner reads the change and asks about anything unclear. Answer in full.

## Session start and end

- Start: read `docs/status.md` and `docs/tasks.md`.
- End: rewrite `docs/status.md`, commit, and push. Write the status as it will be once the session's pull request is merged, because the next session reads it from `main`.
