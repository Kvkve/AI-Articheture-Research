# 0001 Division of work: the main agent coordinates, one party writes code at a time

- Status: Accepted
- Date: 2026-11-23

## Background

The main agent runs on the most expensive model and has a limited context window. The owner wants it to coordinate and to hand code writing to cheaper subagents. Research shows that several agents writing code in parallel cost more and often do no better. The owner has also seen a main agent start more than ten subagents at once, use up the token allowance, and finish none of the tasks.

## Options

1. The main agent writes all code. Subagents only research and review.
2. The main agent coordinates and hands code writing to one subagent at a time.
3. Several subagents write different parts in parallel.

## Decision

Option 2. The flow is: one subagent writes, a different subagent reviews, and the result returns to the main agent, which verifies it.

## Reasons

- Measured data argues against option 3. Agent teams cost 1.8 to 5.1 times as much as a single agent, and only 1 of 4 comparisons was clearly better. Two agents that each wrote a part and then merged succeeded about half as often as one agent alone.
- In option 2 only one party changes code at any moment, so the problems of parallel writing do not arise. File reading, test runs and error output stay in the subagent's context, not the main agent's.
- The only evidence against option 2 is one developer's experience on one project: no mix of a strong planner and a cheaper executor beat the strong model working alone.

## Costs and safeguards

- A subagent knows only what the brief says. A poor brief leads to wrong work. What a brief must contain is in `CLAUDE.md`.
- A subagent may report "done" when it is not. The main agent must read the diff and run the checks itself.
- Usage can run away. The rules in `CLAUDE.md` under "Using subagents" limit this: one code writer at a time; at most three parallel subagents, for read-only research only, and more needs the owner's approval; no nested subagents; a named model for every subagent; a commit after each accepted piece; at most two review rounds.
- Two of these limits are enforced by settings, not only by words: `.claude/settings.json` sets the concurrent limit to 3 and turns off nested subagents. The `implementer` definition also denies it the tool that starts subagents.
- Default models: `implementer` and `reviewer` use Opus, `researcher` uses Sonnet. This is a starting point, to be adjusted from results.

## Evidence

`docs/research/reports/AI 协作开发工作流调研.md`, section "只让一个代理写代码，便宜模型负责读和审".
