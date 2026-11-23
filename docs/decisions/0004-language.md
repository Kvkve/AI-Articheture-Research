# 0004 Language: English in the repository, Chinese for the owner's reading

- Status: Accepted
- Date: 2026-11-23

## Background

The owner's first language is Chinese, and conversation with the AI is in Chinese. The project is meant to inform a later build in a company environment, where the working language is English. An AI reads both languages, so the choice depends on the human readers.

## Options

1. Everything in Chinese.
2. Everything in English.
3. English for repository files, Chinese for conversation and for material written for the owner to read.

## Decision

Option 3.

| Content | Language |
|---|---|
| Rule files, agent definitions, README, decision records, task list, status file | English |
| Code, comments, commit messages | English |
| Learning notes in `docs/learning/` | Chinese |
| Research reports written for the owner | Chinese |
| Conversation | Chinese |

## Reasons

- Technical terms are English in documentation, error messages, tool interfaces and workplace discussion. Reading the project files in English builds that vocabulary.
- One simple rule with two exceptions is easier to follow than a choice per file.
- The owner expects to be the only reader of this repository, so option 1 would also work. The owner chose English for the vocabulary practice.

## Costs and safeguards

- The owner may approve an English rule without fully understanding it. To prevent this, each rule and decision is explained in Chinese in conversation before approval, and English is written in short sentences with common words. A sentence the owner finds hard to read is rewritten.
- The research report that already exists stays in Chinese.
