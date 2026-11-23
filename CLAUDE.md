@AGENTS.md

# Rules for Claude Code

## Division of work

- The main agent designs, splits work into tasks, writes task briefs, verifies results, and explains to the owner. It makes changes of a few lines itself.
- Code is written by `implementer`. Research is done by `researcher`. Review is done by `reviewer`, which must not be the agent that wrote the code.
- A subagent's "done" is a claim. The main agent reads the diff and runs the checks itself before accepting.
- At most two review rounds. If a disagreement remains, the owner decides.
- Agents do not edit code the owner wrote by hand. They give comments only.

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

- Explain each term in plain words the first time it appears. The owner knows SQL well and has studied Java and Python: start from those when introducing a new idea.
- After each change, say what was done and why.
- At each milestone: ask the owner to predict the result before showing it; leave one small piece with a real design choice for the owner to write; ask the owner to explain it back, then fill the gaps.
- For a design choice, give two or three options with the cost of each. The owner chooses. Record it as a decision.

## Session start and end

- Start: read `docs/status.md` and `docs/tasks.md`.
- End: rewrite `docs/status.md`, commit, and push.
