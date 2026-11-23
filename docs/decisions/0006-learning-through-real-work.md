# 0006 Learning: through real work, with the overall design and key decisions first

- Status: Accepted
- Date: 2026-11-23
- Supersedes: [0003](0003-learning-process.md)

## Background

Decision 0003 had the owner predict results, explain finished work back, write selected parts by hand, and pass a self-test at each milestone. These steps were first used in the M1 lesson on 2026-11-23. The owner objected: the project is not a class. The owner wants to learn and to write only when it serves real work or helps to understand what the agent did.

The owner also said that learning all of frontend and backend design and programming at once is not realistic. The owner's learning should centre on the overall design and the key decisions, not on every detail from the start.

## Options

1. Keep 0003: prediction, explain-back, hand-written parts as practice, a self-test at each milestone.
2. Drop the quiz-style steps. Keep the owner's part in real work: the owner makes each design choice and gives the reason, and reads each change before merging it.
3. Drop all learning practices. The agent builds and the owner reads when the owner wishes.

## Decision

Option 2. The practices are in `CLAUDE.md` under "Teaching". The milestone line under "Definition of done" in `AGENTS.md` changes to match.

- Learning follows the project. The agent explains what the current work needs and does not teach topics ahead of need.
- The owner's focus is the overall design and the key decisions: what the parts are, how one request travels through them, where data lives, and why each choice was made. Implementation details are black boxes until the owner asks or a decision depends on them.
- The owner makes each design choice and gives the reason in one sentence. The reason goes into the decision record.
- The owner reads each change before merging it and asks about anything unclear.
- No prediction questions, no explain-back questions, no practice exercises. The owner writes a part by hand only when the owner wants to and the part goes into the product.

## Reasons

- The evidence behind 0003 shows that people who hand all the work to an AI learn less, and that those who learned well asked about concepts and asked for explanations. It supports taking part. It does not single out quizzes.
- Option 2 keeps the owner taking part where the work is real: choices, reasons, reading changes, asking questions.
- A practice that the owner finds pointless is unlikely to last over a long project. This is an inference.
- Option 3 is the pattern the evidence warns against.

## Costs and safeguards

- Explain-back finds gaps that the owner does not know about. Without it, a gap can stay hidden until it leads to a wrong choice. Two things stand in for it. The agent checks the owner's reason for each design choice and says so when it shows a misunderstanding. The owner reads each change before the merge.
- There is no evidence that these two are enough. Look back at the end of M2.
- Treating details as black boxes can hide a detail that matters. The agent must raise a detail when a decision depends on it.

## Finished work this changes

- M0: the task "Owner's self-test for M0" is dropped.
- M1: the task "First concept lesson" keeps its explanation, which was given in conversation on 2026-11-23. Its three explain-back questions and its SQL exercise are withdrawn.
- Nothing was recorded in `docs/learning/` under 0003.

## Evidence

`docs/research/reports/AI 协作开发工作流调研.md`, section "让 AI 写代码可以，让 AI 替你思考不行". The owner's statements in conversation on 2026-11-23.
