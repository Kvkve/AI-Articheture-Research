# 0005 Branching and merging: `main` holds approved work, each task gets a branch

- Status: Proposed
- Date: 2026-11-23

## Background

Until now all work sat on one working branch. The owner proposed creating `main`, doing each piece of work on its own branch, and merging it when ready. What is still open is how a branch reaches `main` and who performs the merge.

Terms: a branch is a separate line of work that does not affect `main` until it is merged. A pull request is a page on GitHub that shows exactly what a branch would change and waits for someone to merge it.

## Options

1. One branch per task. A pull request shows the change. The owner merges it.
2. One branch per task. The main agent merges after the reviewer passes it.
3. All work goes directly to `main`.

## Decision

Proposed: option 1.

## Reasons

- Research found that practitioners keep the merge decision with a human. The merge is the point where "done" is checked.
- A pull request gives the owner one page with the full change. It is a good place to read code, to ask questions, and to give the change to another vendor's model for review.
- Automatic checks can later run on every pull request, where an agent working in a local session cannot switch them off.
- In a Claude Code cloud session, each session works on its own branch, so "one branch per task" matches how the tool already works.

## Costs and safeguards

- Each task needs one more step from the owner: open the pull request page and merge.
- The main agent does not push to `main` directly. The one exception was creating `main`, which the owner approved.

## Evidence

`docs/research/reports/AI 协作开发工作流调研.md`, section "只让一个代理写代码，便宜模型负责读和审", on which decisions stay with the human.
