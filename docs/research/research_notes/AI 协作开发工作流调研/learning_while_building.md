# Learning software architecture and code while an AI agent implements (research notes, as of 2026-11-23)

Method and provenance legend (read first)
- [FETCHED] = I fetched the page with WebFetch. The fetch tool returns a model-generated extraction, not raw text, so numbers should be spot-checked before quoting in a final report. [SNIPPET] = seen only in a search-result summary; I did not open the source. [PDF-UNREADABLE] = fetch failed to decode.
- Evidence tags: MEASURED (controlled study or survey), VENDOR (company claim or docs), PRACTITIONER (blog/anecdote), SECONDARY (press coverage of a study).
- Search used about 18 calls; queries contained no personal or project details. Not covered in depth: spaced repetition specifically, concept-map evidence, Cursor/Copilot/Codex learning features, ADR-for-learning (as opposed to ADR-for-agents). These are listed under Gaps.

## 1. What does research say about AI assistance and skill formation? Which interaction patterns go with learning vs. not?

### Takeaway
The best direct evidence (Anthropic RCT, Jan 2026) shows that novices who delegated code writing learned less than those who coded by hand, while those who used the AI to ask conceptual questions or to get explanations alongside code kept most of the learning. Education RCTs agree: unrestricted answer-giving AI raises practice performance but lowers later unaided performance; guardrailed tutors that withhold full answers largely avoid the harm. All effects are measured on short horizons and small or context-specific samples, and none tests agentic tools or architecture learning.

### Cited Findings
- Anthropic RCT, "How AI Impacts Skill Formation" (Shen and Tamkin, published 2026-01-29): 52 mostly junior engineers, all with 1+ year of weekly Python, learned the unfamiliar Python async library Trio; AI group had a sidebar assistant that could see their code; control coded by hand. 35-minute task, then 25-minute quiz. [FETCHED, VENDOR-authored MEASURED] — [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills); preprint [arXiv 2601.20245](https://www.arxiv.org/pdf/2601.20245) [PDF-UNREADABLE; only title, authors, version v2 and reference list read]
- Result: quiz about 50% (AI) vs about 67% (hand-coding), Cohen's d = 0.738, p = 0.01; largest gap on debugging questions. Completion about 2 minutes faster with AI (about 23 vs 25 min), not significant (p = 0.391). The page text says 67%, but its chart labels about 65%; minor inconsistency. — [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills) [FETCHED]. ITPro reported 51 participants vs 52 elsewhere [SNIPPET] — [search summary listing](https://www.itpro.com/software/development/anthropic-research-ai-coding-skills-formation-impact)
- Interaction patterns (only 24 of 52 clustered; groups of 2 to 7, so very small): LOW scorers (<40% avg): AI delegation (n=4, 39%, fastest), progressive AI reliance (n=4, 35%), iterative AI debugging (n=4, 24%, slowest). HIGH scorers (>=65%): generation-then-comprehension (n=2, 86%), hybrid code-explanation (n=3, 68%), conceptual inquiry (n=7, 65%, second fastest). — [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills) [FETCHED]
- Authors' own limitations: small sample; immediate comprehension, not long-term retention; patterns are associational not causal; one library and one chat-sidebar setup that differs from agentic tools like Claude Code, which they expect "could" have a larger effect on skill; productivity gain not significant. Authors suggest getting stuck / cognitive effort supports mastery and point to learning modes as design examples. — [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills) [FETCHED]. Commentary noted it covers learning a new library, not general programming ability — [InfoQ](https://www.infoq.com/news/2026/02/ai-coding-skill-formation) [SNIPPET]
- Bastani et al., PNAS 2025 (vol 122, issue 26), "Generative AI Without Guardrails Can Harm Learning": high school math, Turkey, fall 2023, about 1,000 students (one summary says 839 analyzed). Unrestricted GPT-4 ("GPT Base") group scored 48% better during practice but 17% worse than control on the later unaided exam; "GPT Tutor" (prompted with teacher-written hints, not giving answers) largely mitigated the harm. Limitation: single school, math. — [Wharton summary](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education), [SSRN](https://papers.ssrn.com/abstract=4895486), [PsyPost](https://www.psypost.org/unrestricted-generative-ai-harms-high-school-math-learning-by-acting-as-a-crutch/) [all SNIPPET; MEASURED]
- Kestin et al., Scientific Reports, June 2025: Harvard physics, N=194, RCT; a purpose-built AI tutor (revealed one step at a time, did not give whole solutions) produced median learning gains over twice those of an in-class active-learning lesson, with higher engagement. One course, one institution, short-term; lead author says it is not an argument to replace human interaction. — [PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC12179260/), [Harvard Gazette](https://news.harvard.edu/gazette/story/2024/09/professor-tailored-ai-tutor-to-physics-course-engagement-doubled/) [SNIPPET; MEASURED]
- Fan et al., "Beware of metacognitive laziness," BJET 2024 (arXiv Dec 2024): 117 students, 4 conditions (ChatGPT, human expert, checklist, none); ChatGPT group improved essay scores most but showed no significantly different knowledge gain or transfer; engaged less in metacognitive activity and copy-pasted despite prompts. Abstract-level only; I did not open the journal page. — [arXiv 2412.09315](https://arxiv.org/abs/2412.09315v1) [SNIPPET; MEASURED]
- Gerlich, Societies 15(1):6, Jan 2025: survey of 666 people plus 50 interviews; frequent AI use correlated negatively with critical-thinking scores, mediated by cognitive offloading; younger people worse; author stresses correlation not causation; a correction dated 2025-09-10 exists whose content I did not check. — [PsyPost](https://www.psypost.org/ai-tools-may-weaken-critical-thinking-skills-by-encouraging-cognitive-offloading-study-suggests/), [SSRN](https://papers.ssrn.com/abstract=5082524) [SNIPPET; MEASURED, weak design (cross-sectional self-report)]
- NN/g, "Vibe Architects" (Moran and Gibbons, 2026-06-19): 7 nontechnical people using agentic tools (Claude Code/Cowork); they built working systems but could not explain how they worked; learned mainly via experimentation and community content (YouTube, Reddit, Slack), not from the products; often approved permission prompts unread; systems decayed over time. Tiny, hard-to-recruit sample, self-reports plus observed sessions. — [NN/g](https://www.nngroup.com/articles/vibe-architects/) [FETCHED; MEASURED-qualitative]. (A search summary claimed all seven found the tools "consistently failed as a source of learning"; the fetched text says the products offered little onboarding and learning came from elsewhere, so treat that stronger phrasing as unverified.)
- "Cognitive debt" framing: Margaret-Anne Storey's student-team example (by weeks 7-8 the team could not make simple changes; no one could explain design decisions or how parts fit; "the theory of the system ... had fragmented or disappeared"); Willison reports the same after prompting features without reviewing code. — [Willison, 2026-02-15](https://simonwillison.net/2026/Feb/15/cognitive-debt) [FETCHED; PRACTITIONER, one case]
- Geoffrey Litt (via Willison, 2026-07-02): you need "a rich set of concepts in your mind" to participate in the creative process with an agent; learn what the agent is doing to stay a participant. — [Willison, July 2026](https://simonwillison.net/2026/Jul/2/) [FETCHED; PRACTITIONER]
- Counter-context on productivity (not learning): METR early-2025 RCT found experienced open-source developers 19% slower with AI; Feb 2026 follow-up estimated -18% with CI -38% to +9% and says selection effects (developers refusing to work without AI) bias it, and that tools have improved. — [METR update](https://metr.org/blog/2026-02-24-uplift-update/) [SNIPPET; MEASURED]. Relevance: speed claims and learning claims are separate; do not infer learning from productivity.
- OpenAI reported preliminary, self-run exam results for ChatGPT study mode (March 2026), with acknowledged technical/onboarding issues; conflict of interest. — [OpenAI](https://openai.com/index/understanding-ai-and-learning-outcomes/) [SNIPPET; VENDOR]

### Inferences
- Consistent across Anthropic RCT, Bastani and Fan: the harm comes from the AI supplying the thinking (answers, finished code), not from AI being present. The protective factor in each is that the learner still does the cognitive step (asks "why", attempts first, checks understanding) or the tool withholds the answer.
- For the target learner the transferable rule is: after the agent produces something, ask for the concept, then verify yourself; avoid the "paste error back to AI until it passes" loop (the slowest and lowest-scoring pattern in the Anthropic study).
- Extrapolation risk: the evidence is on a library-learning task of about an hour with a chat assistant. Effects on multi-week architecture understanding with an autonomous agent are unmeasured; NN/g and Storey are the only (weak) signals and they point the same direction.
- Caution on the pattern clusters: n of 2 to 7 per pattern, associational; usable as hypotheses for practice, not as proof.

### Gaps
- No controlled study found on learning architecture (as opposed to syntax/library use) with agentic AI, nor on analysts transitioning to web development.
- No long-term (weeks to months) retention data for AI-assisted coding learners.
- Arxiv items surfaced in search but not opened: 2604.17460 and 2607.08849 (titled "Experimental Evidence on the Learning Impact of Generative AI"); possibly relevant newer evidence, unverified.
- Bastani, Kestin, Fan, Gerlich were not read in full; verify numbers against journal pages before final citation.

## 2. Which practical techniques are recommended and what supports each?

### Takeaway
Direct measured support in AI-coding contexts exists only for the broad principle (stay cognitively active; ask for explanation/concepts; withhold answers). Individual techniques (teach-back, predict-then-reveal, worked examples, retrieval, spaced review) have general learning-science support but little or no testing in AI-assisted coding for novices; one retrieval-with-worked-examples literature is mixed.

### Cited Findings
- Retrieval practice/quizzing generally: classroom meta-analysis about Hedges' g = 0.50, lab meta-analysis similar, high heterogeneity. — [search summary of literature](https://link.springer.com/article/10.1007/s10648-015-9297-3) [SNIPPET; MEASURED, general education]
- Retrieval after worked examples is inconsistent: several experiments found no benefit over restudy for problem-solving skills (explained by novice cognitive load); a 2025 study reports benefit when retrieval is embedded stepwise within worked examples. — [Utrecht repository](https://research-portal.uu.nl/en/publications/retrieval-practice-in-stepwise-worked-examples-improves-learning/), [Utrecht Testing.pdf](https://dspace.library.uu.nl/bitstream/handle/1874/327549/Testing.pdf?sequence=1) [SNIPPET]. Implication: for a novice, test on small pieces right after a worked example, not on whole problems.
- Self-explanation meta-analysis exists (Bisra et al., 2018), cited in a 2022 ACM review of worked examples in programming; I did not read either. — [ACM review](https://doi.org/10.1145%2F3560266) [SNIPPET]
- Product-design evidence for step-wise withholding: Kestin tutor gave one step at a time; Bastani guardrailed tutor gave hints not answers; both beat or matched the alternative. — see Q1 sources.
- Anthropic study's high-scoring behaviours map to: predicting/asking concepts first ("conceptual inquiry"), then requesting explanation with code ("hybrid"), or generating code and then interrogating it ("generation-then-comprehension"). — [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills) [FETCHED]
- Explain-back / teach-back, predict-before-reveal, decision memos, glossaries/concept maps, spaced review: I found no source testing these specifically with AI coding assistance. (Illusion of explanatory depth in programming: also not found.)

### Inferences (practice design, my synthesis, not sourced as proven)
Ranked by learning per minute for a time-limited learner, hedged accordingly:
1. Ask conceptual "why/what would break if" questions after each agent change (about 2-5 min; closest to the Anthropic high-scoring patterns).
2. Predict-before-reveal on one diff or one request path per milestone (1 line written before running or reading).
3. Own one small piece by hand per milestone (Learning-style TODO(human)); pick pieces with a real design decision.
4. Explain-back: write 3-5 sentences of what the change does and why, then have the agent critique for errors (exposes illusion of understanding).
5. Decision memo: agent offers 2-3 options with trade-offs; learner chooses and records reason (also becomes the ADR).
6. Quiz-yourself cards or a 5-question end-of-milestone check, revisited a week later (spaced review); keep tiny.
Skip or minimize: full concept maps, exhaustive glossaries; keep a short glossary of only terms that blocked you.

### Gaps
- No direct evidence on decision memos, concept maps, glossaries, or spaced review in this setting; evidence is by analogy.
- Did not search specifically for spaced repetition or predict-observe-explain literature; worth a follow-up.

## 3. Tool features supporting learning (as of late 2026) and reported experience

### Takeaway
Claude Code ships built-in Explanatory and Learning output styles plus custom styles; docs are clear about behavior, but I found essentially no independent measured evidence or substantial user experience reports for effectiveness. ChatGPT Study mode and Gemini Guided Learning exist as general-chat equivalents; evidence is vendor-preliminary or anecdotal.

### Cited Findings
- Claude Code output styles (official docs): built-ins are Default, Proactive, Concise, Explanatory, Learning. Explanatory adds "Insight" blocks (2-3 points explaining choices in the codebase). Learning adds the same Insights and also leaves `TODO(human)` markers, then issues a "Learn by Doing" request (context, task, guidance) and stops until you finish, then comments on your code. Switch with `/output-style <style>` (v2.1.269+) or `/config`; setting `outputStyle` value is case-sensitive; custom styles are Markdown files in `~/.claude/output-styles` or `.claude/output-styles`; `keep-coding-instructions: true` retains coding instructions. Styles are instructions, not guarantees; CLAUDE.md, skills and hooks are the tools for knowledge, tasks and guarantees; Explanatory/Learning produce longer output (more tokens); subagents do not inherit styles. — [Claude Code docs](https://code.claude.com/docs/en/output-styles) [FETCHED; VENDOR]
- Note: docs say non-default styles exclude some built-in engineering instructions (scope, testing) unless `keep-coding-instructions` is set for custom styles; built-in learning styles are described as keeping them ("Each of the four other built-in styles keeps those instructions"). Earlier search summary said the opposite for built-ins; the fetched page is authoritative. — [Claude Code docs](https://code.claude.com/docs/en/output-styles) [FETCHED]
- Launch coverage: learning mode was first limited to Claude for Education, later made available to all, including Claude Code. — [Engadget](https://www.engadget.com/ai/anthropic-brings-claudes-learning-mode-to-regular-users-and-devs-170018471/), [Inc.](https://www.inc.com/ben-sherry/anthropic-is-making-it-even-easier-to-learn-how-to-code/91227443) [SNIPPET; date not captured, likely 2025]
- Experience reports: a Tessl analysis characterizes Learning as pair-programmer stepping in/out and Explanatory as narrating teacher; a community guide warns Learning mode is too slow for urgent production work. No outcome data. — [Tessl](https://tessl.io/blog/claude-code-now-lets-you-customize-its-communication-style/), [azukiazusa.dev](https://azukiazusa.dev/en/blog/claude-code-learning-mode) [SNIPPET; PRACTITIONER]
- Anthropic's own study cites the Learning/Explanatory modes and ChatGPT Study Mode as examples of designs for skill development, but did not test them. — [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills) [FETCHED]
- ChatGPT Study mode and Gemini Guided Learning: only OpenAI's preliminary self-reported study and informal single-tester comparisons found; a 2026 Mashable roundup says no evidence they improve grades. — [OpenAI](https://openai.com/index/understanding-ai-and-learning-outcomes/), [Lifehacker JP](https://www.lifehacker.jp/article/2508-chatgpt-vs-gemini-study-mode/), [Yahoo/Mashable](https://tech.yahoo.com/ai/articles/put-chatgpt-gemini-study-modes-123000726.html) [SNIPPET]
- OpenAI Codex has a "codebase onboarding" use case page. — [OpenAI developers](https://developers.openai.com/codex/use-cases/codebase-onboarding) [SNIPPET; not read]

### Inferences
- A style is a nudge the model can drop; the Anthropic data suggest what matters is the learner's behavior. Learning style's TODO(human) forces one hands-on step per design decision, which fits the "do the thinking" principle but is untested. Using Explanatory by default and Learning for selected milestones (not all work) fits limited time.
- A custom project style or CLAUDE.md rule (for example "before implementing, ask me to predict; after, give 3 check questions") is feasible per docs but unvalidated.

### Gaps
- No independent evaluation of Claude Code Learning/Explanatory; Reddit/HN threads not searched successfully.
- Cursor, Copilot, Gemini CLI, Codex learning-oriented features not researched. Publication dates of the Claude learning-mode launch not confirmed. Docs reflect specific versions (v2.1.2xx); check current version.

## 4. How do experienced engineers recommend non-experts learn architecture through a real project?

### Takeaway
Practitioner consensus (not measured evidence): keep a working mental model of the system's parts, data flow and why decisions were made; trace one real request end to end; read data model and tests; treat implementation details as replaceable. Skeptical voices say non-experts delegating architecture produce brittle systems and cannot judge them.

### Cited Findings
- Common guidance for unfamiliar code: start at entry points (routes/main), follow one real user action (HTTP request, router, handler, service, database, response), then a second request touching different parts; read tests as behavior docs; start from schema/types; run the smallest test or route to confirm your trace. Sources are lightweight blogs; treat as heuristics. — [CoderLegion](https://coderlegion.com/12355/the-developers-guide-to-understanding-any-codebase), [Scrimba](https://scrimba.com/articles/how-to-understand-a-new-codebase-fast-2026/), [Claudefolio](https://claudefolio.com/blog/how-to-read-code-you-didnt-write), [library guide](https://library-d7m.pages.dev/developer-productivity/reading-code/navigating-unfamiliar-codebases) [SNIPPET; PRACTITIONER]
- Cognitive-debt / mental-model view: what must be kept is the "theory of the system" (what it should do, how intentions map to implementation, how to change it), which lives in heads not code. — [Willison on Storey](https://simonwillison.net/2026/Feb/15/cognitive-debt) [FETCHED]
- Skeptical: HackerNoon "AI can code your app, just don't let it architect it" and InfoQ both argue that without architectural direction the output is suboptimal or throwaway. Neal Ford and Sam Newman are described as skeptical of piling more context files onto agents. — [HackerNoon](https://hackernoon.com/ai-can-code-your-appjust-dont-let-it-architect-it), [InfoQ](https://infoq.com/articles/ai-agents-improve-software-architecture), [O'Reilly](https://www.oreilly.com/radar/?p=18521) [SNIPPET; PRACTITIONER]
- Optimistic: DHH is reported to say a non-coder who understands the problem and can judge the result directly can sometimes outperform coders using AI; behind a members-only wall. — [ITNEXT](https://itnext.io/ruby-on-rails-creator-says-non-coders-can-sometimes-outperform-coders-with-ai-ab7e7c7aeef4) [SNIPPET; PRACTITIONER, paywalled]
- NN/g: non-technical agent users could not explain their systems and gave minimal oversight. — [NN/g](https://www.nngroup.com/articles/vibe-architects/) [FETCHED]

### Inferences
- "Deep vs black box" is not given by a source I read in full; a reasonable split for this learner: understand deeply (a) the data model and its constraints (the analyst's SQL strength transfers), (b) the request lifecycle and where state lives, (c) boundaries between frontend/backend/DB and what crosses them, (d) auth and error handling at concept level, (e) why each major choice was made. Treat as black box initially: build tooling, CSS details, framework internals, deployment plumbing, boilerplate. Mark this as my synthesis.
- One end-to-end request trace per milestone (predict the path, then confirm via logs/debugger/agent-generated sequence diagram) is the highest-leverage exercise supported by practitioner consensus; no measured evidence.

### Gaps
- No primary writings by named senior engineers (Fowler, Beck, Newman etc.) on non-expert architecture learning were read in full; only search summaries.
- No source explicitly defining a "black box vs deep" boundary for novices.

## 5. Storing learning materials in the repo without staleness

### Takeaway
Practitioners agree staleness is the central risk and that stale records mislead agents as well as people. Fixes: immutable dated records superseded rather than edited, generated indexes with CI checks, or a single short living design doc. All is practitioner opinion; none is measured.

### Cited Findings
- ADRs help agents but stale ones are followed "with full confidence"; one author saw an agent preserve an obsolete abstraction because an ADR still called it mandatory; suggested marking records binding/proposed/superseded and letting agents question outdated decisions. — [O'Reilly Radar, "Coding agents love decision records"](https://oreilly.com/radar/coding-agents-love-decision-records/) [SNIPPET; PRACTITIONER]
- Make merged records immutable and supersede with new ones; generate the index from frontmatter and fail CI if out of date; "AI checks; humans attest." — [Codeminer42](https://blog.codeminer42.com/stale-docs-are-prompt-injection-you-wrote-yourself/) [SNIPPET; PRACTITIONER]
- Counter-view: append-only decision logs become an archive that is hard to read for current state; prefer a short capped DESIGN.md edited in place, with local context in code comments. — [DEV Community](https://dev.to/gregsmethells/your-decision-log-is-an-archaeological-site-41bk) [SNIPPET; PRACTITIONER]
- ADRs as separate files "routinely go stale" (synchronization problem); proposed alternative is structured knowledge in git commit messages. — [arXiv 2603.15566](https://arxiv.org/pdf/2603.15566) [SNIPPET; preprint, unread]

### Inferences
- Learning notes differ from ADRs: tie each note to a milestone (dated, never edited after the milestone closes) and link it from the ADR/decision it explains; a note is a snapshot of "what I understood then", so staleness is acceptable if clearly dated and not read by agents as rules. Keep notes out of paths the agent auto-loads (CLAUDE.md/AGENTS.md) or label them "learner notes, not authoritative". Only the current-state architecture doc and ADR index need maintenance. This is my synthesis; the sources address ADRs, not learner notes.
- Cheap anti-staleness: link notes to commit hashes/tags; put the end-to-end trace as a test or script that fails when the path changes (not sourced).

### Gaps
- No source on learner-notes-in-repo specifically. Sources are blogs of unknown reach; none read in full.

## 6. Pitfalls (illusion of understanding, passive reading, over-reliance): detection and countermeasures

### Takeaway
Evidence shows passive acceptance and fluent-seeming output are real risks (lower comprehension, metacognitive laziness, inability to explain own systems), but I found no validated detection method for AI-coding learners. Practical detection is behavioral self-tests: can you predict, explain, or modify without the agent?

### Cited Findings
- Learners with AI engaged less in self-monitoring and evaluating their work, despite equal or higher performance scores ("metacognitive laziness"): performance can look good while knowledge gain and transfer do not differ. — [arXiv 2412.09315](https://arxiv.org/abs/2412.09315v1) [SNIPPET]
- Practice performance rose 48% while unaided performance fell 17% with unrestricted AI: performance with AI is a poor proxy for learning. — [Wharton](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education) [SNIPPET]
- Debugging was the biggest quiz gap in the Anthropic study; iterative AI debugging had the lowest scores. — [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills) [FETCHED]
- Non-technical agent users approved permission requests without reading them and could not explain systems that worked. — [NN/g](https://www.nngroup.com/articles/vibe-architects/) [FETCHED]
- Cognitive debt: inability to make simple changes without breakage is the observable symptom. — [Willison](https://simonwillison.net/2026/Feb/15/cognitive-debt) [FETCHED]
- Offloading correlated with lower critical thinking (correlational only). — [PsyPost on Gerlich](https://www.psypost.org/ai-tools-may-weaken-critical-thinking-skills-by-encouraging-cognitive-offloading-study-suggests/) [SNIPPET]
- Disagreement/nuance: AI tutoring that is designed for pedagogy can beat in-class active learning (Kestin) and guardrails largely remove harm (Bastani), so "AI harms learning" is conditional on design and use. Also the Anthropic authors note productivity gains were not significant in their task, and METR's follow-up is inconclusive, so neither "AI always helps" nor "AI always hurts" is supported. — sources above.

### Inferences
Detection tests (my synthesis): (1) "Close the chat" test: can you explain the change or predict behavior without the agent, in 2 minutes? (2) Can you make a small modification yourself? (3) Count how often you pasted errors back without reading; (4) a weekly 5-question self-quiz on the system; (5) can you answer "what breaks if I remove X?" Counters: predict-first, explain-back with agent critique, one hand-written piece per milestone, conceptual questions before code requests, reading diffs not summaries, a time cap so the learning load stays small.

### Gaps
- No validated instrument for illusion of understanding in AI-assisted coding found. Illusion-of-explanatory-depth research (Rozenblit and Keil) not searched directly.
