# 0003 Learning: the owner joins each decision, writes some parts by hand, and self-tests at each milestone

- Status: Superseded by [0006](0006-learning-through-real-work.md)
- Date: 2026-11-23

## Background

The owner knows SQL well, has studied Java and Python, and has not built a web backend, a frontend or a system architecture before. One goal of the project is for the owner to learn, and later to take part in review. Research shows that people who hand all the coding to an AI learn clearly less. A common result is a system that runs while its owner cannot explain how.

## Options

1. The AI writes everything. The owner reads the code and the explanations.
2. The owner takes part in each design choice, writes selected parts by hand, and tests understanding by predicting and explaining back.
3. The owner writes most of the code. The AI only tutors.

## Decision

Option 2. The practices are in `CLAUDE.md` under "Teaching".

## Reasons

- In a controlled experiment, beginners who coded with an AI scored about 50 on a quiz, against about 67 for those who coded by hand. High scorers asked about concepts and asked the AI to explain. Low scorers pasted errors back to the AI again and again.
- Option 1 is close to the low-scoring pattern. Option 3 is too slow and goes beyond what the owner asked for, which was to learn without mastering every detail.
- Learning focuses on the data model, the full path of one request, what passes between frontend, backend and database, and the reason for each decision. Styling, build tools and framework internals are treated as black boxes at first.

## Costs and safeguards

- Progress is slower. The owner has accepted this.
- These practices come from general research on learning. Nobody has tested them for a non-professional developer running a long project with agent tools.
- The test: at the end of each milestone, can the owner explain the finished part without looking at the conversation, and make one small change alone? If not, fill the gap before moving on.

## Evidence

`docs/research/reports/AI 协作开发工作流调研.md`, section "让 AI 写代码可以，让 AI 替你思考不行".
