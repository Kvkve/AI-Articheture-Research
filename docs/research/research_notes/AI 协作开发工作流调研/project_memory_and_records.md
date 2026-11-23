# Project memory and records for long-running AI-assisted projects (state of practice, Nov 2026)

Evidence labels: [FULL] = page fetched and read (via fetch tool, which summarizes with a small model, so treat quotes as approximate); [SNIP] = seen only in search-result summaries; [VENDOR] / [PRACT] (practitioner) / [MEAS] (measured study). Today = 2026-11-23. Research budget was ~15 tool calls, so coverage of Kiro, Cline Memory Bank and BMAD primary docs is thin (see Gaps).

## 1. What do vendor write-ups recommend for long-running agent work?

### Takeaway
Both vendors converge on: a small number of durable repo artifacts, a machine-checkable task list, an append-style progress log, git commits as checkpoints, and a short entry-point file that points to deeper docs. OpenAI adds active mechanisms against rot (doc linters, a doc-gardening agent). Anthropic's own current Claude Code docs say conversation state is lost on new sessions and compaction, so persistent rules belong in CLAUDE.md.

### Cited Findings
- Anthropic engineering, "Effective harnesses for long-running agents" (published 2025-11-26, Justin Young) [FULL, VENDOR]: an initializer agent writes a JSON feature list (200+ end-to-end features in the example, each with category, description, steps and a `passes` flag, all initially failing); coding agents may change only `passes`; prompt says it is "unacceptable to remove or edit tests". JSON was chosen because models are less likely to overwrite it inappropriately than Markdown. — [Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Same article: `claude-progress.txt` logs what each session did; `init.sh` starts the dev server plus a basic end-to-end test; initializer makes an initial git commit; coding agents commit after each change with descriptive messages so bad changes can be reverted. — [Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Same article, session start ritual: `pwd`, read progress file and git log, read feature list, pick highest-priority unfinished feature, run `init.sh` and smoke-test to catch bugs left by earlier sessions. End ritual: leave code in a clean mergeable state, commit, update progress file. — [Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Same article, failure modes and fixes: one-shotting the app and running out of context (fix: feature list, one feature at a time); later agent declares project done early (fix: failing features visible); features marked done without e2e testing (fix: browser-automation self-verification). — [Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- OpenAI, "Harness engineering" (published 2026-02-11, Ryan Lopopolo) [FULL, VENDOR]: AGENTS.md kept ~100 lines, acts as a table of contents pointing to deeper sources; one big AGENTS.md failed (crowded out task context, went stale, hard to verify mechanically). — [OpenAI](https://openai.com/index/harness-engineering/)
- Same article, `docs/` as system of record: root `ARCHITECTURE.md`; `docs/design-docs/` (indexed, with verification status); `docs/exec-plans/{active,completed}/` plus `tech-debt-tracker.md`; `docs/generated/db-schema.md`; `docs/product-specs/`; `docs/references/*llms.txt`; top-level `DESIGN.md`, `FRONTEND.md`, `PLANS.md`, `PRODUCT_SENSE.md`, `QUALITY_SCORE.md`, `RELIABILITY.md`, `SECURITY.md`. — [OpenAI](https://openai.com/index/harness-engineering/)
- Same article, execution plans: small changes get ephemeral lightweight plans; complex work gets checked-in execution plans with progress and decision logs. — [OpenAI](https://openai.com/index/harness-engineering/)
- Same article, anti-rot: a recurring "doc-gardening" agent finds docs that no longer match code and opens fix-up PRs; dedicated linters/CI jobs check the knowledge base is current, cross-linked and structured; custom lint error messages carry remediation instructions for the agent; `QUALITY_SCORE.md` grades each domain/layer and background agents update it. — [OpenAI](https://openai.com/index/harness-engineering/)
- Claude Code official docs, "How Claude Code works" (undated, current docs) [FULL, VENDOR]: each new session starts with a fresh context window; compaction keeps requests and key snippets but "detailed instructions from early in the conversation may be lost"; put persistent rules in CLAUDE.md; a "Compact Instructions" section in CLAUDE.md or `/compact focus on ...` steers what is preserved; sessions are stored as JSONL under `~/.claude/projects/` and can be resumed/forked; file checkpoints are separate from git. — [Claude Code docs](https://code.claude.com/docs/en/how-claude-code-works)

### Inferences
- The Anthropic pattern is sized for autonomous multi-session builds with a test oracle; for a human-driven solo project the minimal transferable parts are: machine-readable "what remains" list, progress/handoff note, frequent commits, a start-of-session smoke test.
- The OpenAI layout is for a team with many parallel agents; its transferable idea is the index-plus-pointers structure and mechanical doc checks, not the full set of top-level files.

### Gaps
- No quantitative evidence from either vendor that these artifacts improve outcomes; both are descriptive experience reports.
- OpenAI article details were read through a summarizing fetch; wording may differ from the original.

## 2. What do spec-driven / agentic frameworks prescribe, and what is the criticism?

### Takeaway
Frameworks prescribe a per-feature spec -> plan -> tasks pipeline (spec-kit, Kiro, BMAD) or a brainstorm -> plan -> execute skill workflow (superpowers). Adoption is huge by star count, but independent critiques (Fowler/Thoughtworks site, practitioners) report verbosity, review burden, and waterfall drift; Thoughtworks Radar Vol. 35 (Nov 2026) puts "AI-driven documentation sprawl" in Caution.

### Cited Findings
- GitHub spec-kit [FULL, repo page]: commands `/speckit-constitution`, `-specify`, `-plan`, `-tasks`, `-implement`, `-converge`; `.specify/memory/` directory; extensions create `.specify/bugs/<slug>/` and `.specify/assessments/<slug>/decision.md`; ~151k stars, 13.6k forks at fetch time. Page did not name spec.md/plan.md/tasks.md or `specs/NNN/` (fetch limitation). — [github.com/github/spec-kit](https://github.com/github/spec-kit)
- Martin Fowler site, "Understanding SDD tools: Kiro, spec-kit, Tessl" (published 2025-10-15; tested Sept 2025, so possibly outdated) [FULL, PRACT]: Kiro = requirements/design/tasks markdown per spec plus steering files (product.md, structure.md, tech.md); a small bug became 4 user stories with 16 acceptance criteria ("sledgehammer to crack a nut"). — [Fowler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- Same article on spec-kit: constitution plus ~8 files per spec, branch per spec; repetitive verbose markdown tedious to review ("would rather review code"); agent ignored research notes and generated duplicate classes; overkill for a mid-sized feature; branch-per-spec suggests change-request lifetime rather than long-lived living specs. — [Fowler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- Same article on Tessl: `.spec.md` mapped 1:1 to code files, KNOWLEDGE.md, "GENERATED FROM SPEC - DO NOT EDIT"; regenerating from same spec gave different code; private beta then. — [Fowler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- obra/superpowers [FULL, repo page]: ~325k stars, 28.8k forks; workflow stages brainstorming -> git worktrees -> writing-plans (2-5 minute tasks with exact paths and verification) -> subagent-driven development/executing-plans -> TDD -> code review -> finish branch; small changes agreed in chat, larger ones get a written design doc; the page names no output directory for plans. — [github.com/obra/superpowers](https://github.com/obra/superpowers)
- Thoughtworks Technology Radar Vol. 35, "AI-driven documentation sprawl" (2026-11-04), ring Caution [FULL, VENDOR/consultancy opinion]: spec-driven tools such as spec-kit and BMAD generate large volumes of Markdown that skip the automated checks code gets; repos become a "big ball of documentation mud"; obsolete/contradictory files waste agent context; advice is to treat Markdown as first-class and prune/consolidate; linked blip "Semantic review of AI-edited prose" (Assess). — [Thoughtworks Radar](https://www.thoughtworks.com/radar/techniques/ai-driven-documentation-sprawl)
- BMAD [SNIP, secondary]: PRD at `docs/prd.md`, architecture at `docs/architecture.md`, sharded stories under `docs/stories/` (BMAD v4-era user guide mirror); critics say for solo developers planning phases carry most value and the implementation pipeline is overhead; mid-project scope changes force updating and re-sharding many files; community guidance suggests full method for roughly 15-30 stories. Newer BMAD versions may have changed layout. — [BMAD user guide mirror](https://cdn.jsdelivr.net/npm/@ptnglobal/bmad-method@4.43.1/docs/user-guide.md); [Limitations of BMAD Method](https://asantos2000.github.io/blog/post-3/); [scale-adaptive planning](https://www.mintlify.com/bmad-code-org/BMAD-METHOD/concepts/scale-adaptive-planning)
- Cline Memory Bank [SNIP; community custom-instruction pattern, not a built-in]: files projectbrief.md, activeContext.md, progress.md etc.; Cline docs advise projectbrief ~one page, activeContext = current state only (not a log), progress = summary not changelog; "update memory bank" trigger makes the agent review every file; staleness/verbosity named as risks in a glossary page, no formal critique or benchmark found. — [Cline docs](https://docs.cline.bot/best-practices/memory-bank); [PromptLayer glossary](https://www.promptlayer.com/glossary/cline-memory-bank)
- SDD-is-waterfall debate [SNIP, PRACT]: critics say spec/plan/tasks before implementation is "waterfall for AI"; defenders say the problem is freezing specs, not writing them; Böckeler's taxonomy (cited via a dev.to post) says most tools are only spec-first with no strategy to maintain specs over time; one source says a feature requirement doc should fit on one screen. — [Scrum.org](https://www.scrum.org/resources/blog/spec-driven-development-isnt-waterfall-unless-youre-using-it-way); [dev.to Pacheco](https://dev.to/pacheco/spec-driven-development-isnt-waterfall-but-it-keeps-ending-up-there-4eei); [Augment Code](https://www.augmentcode.com/guides/spec-driven-development-vs-waterfall)

### Inferences
- Star counts (spec-kit, superpowers) show interest, not retention; no source found measures long-run (multi-month) survival of their artifacts.
- The pattern across critiques: per-feature artifacts accumulate (specs/NNN, stories) with no archive/consolidation step, which is the mechanism behind the Radar's "sprawl" warning.

### Gaps
- Kiro official docs, BMAD v6 current docs, and spec-kit's per-spec file layout were not read directly.
- No measured study comparing SDD frameworks with unstructured use; criticism is practitioner opinion. Fowler article is ~13 months old and tests were from Sept 2025.

## 3. ADR / MADR with AI agents; lightweight ADRs for solo projects

### Takeaway
Practitioners put ADRs in `docs/decisions` and tell the agent in AGENTS.md how to treat each status; the main risks are agents over-obeying obsolete ADRs and ADRs that accrete history. Keeping each ADR to current text with git as changelog is the lightweight recommendation found.

### Cited Findings
- Duncan Davidson, O'Reilly Radar, 2026-10-02 [FULL, PRACT]: ADRs as Markdown in `docs/decisions`; AGENTS.md rules: accepted = binding, proposed = non-binding context, superseded = history; on conflict the agent stops and asks whether task or ADR should change; agent proposes new/updated ADRs for durable decisions; each ADR holds only current text (git is the changelog); each rule stated once and cross-referenced; `Updated:` / `Superseded-On:` date lines. — [O'Reilly](https://oreilly.com/radar/coding-agents-love-decision-records/)
- Same article, pitfalls: an agent kept an outdated storage abstraction and added a layer to satisfy an old ADR; "deliberation creep" (amendments explaining their own history, implementation details promoted to rules). Alternative of immutable, superseded-only ADRs is acknowledged. — [O'Reilly](https://oreilly.com/radar/coding-agents-love-decision-records/)
- Qodo glossary [SNIP, vendor marketing]: an ADR records but does not enforce a decision; needs checks on new code; cites an example of an agent bypassing an ADR. — [Qodo](https://www.qodo.ai/glossary/what-is-an-architecture-decision-record/)
- Tessl registry "adr-skill" (vercel/ai) recommends MADR for decisions with several options [SNIP]. — [Tessl](https://tessl.io/registry/skills/github/vercel/ai/adr-skill)
- A preprint (arXiv 2609.30334 focus-group report) [SNIP; ID as returned by search, unverified] says participants used AI to draft ADRs but wanted human judgment on rationale. A claim of reduced dev time with decision records in a preprint experiment appeared only in a snippet and is unverified. — [arXiv](https://arxiv.org/pdf/2609.30334)

### Inferences
- For a solo owner, a one-page-or-shorter ADR (context, decision, consequences, status) per durable decision, with only accepted/superseded statuses, captures the benefit; full MADR option matrices are only worth it for multi-option decisions.

### Gaps
- No dedicated "solo-project ADR" guidance found; adr.github.io and MADR docs were not fetched.

## 4. Doc sprawl and staleness: causes, mechanisms, lessons learned

### Takeaway
Evidence says stale or generated context files do harm (cost up, success not up), and practitioners/vendors converge on short entry files, single-source-of-truth, mechanical checks and scheduled pruning. Causes of agent file-spamming were not found in a rigorous source.

### Cited Findings
- Gloaguen et al., "Evaluating AGENTS.md" (arXiv 2602.11988, 2026-02-12; ICLR 2026 workshop) [FULL abstract, MEAS]: context files generally do not improve task success, raise inference cost by over 20% on average, results hold across LLMs/agents and for generated and developer-written files; agents follow instructions well but repository overviews do not help; useful for non-standard practices; evaluate before deploying. Preprint version reportedly says LLM-generated files reduced success [SNIP]. — [arXiv](https://arxiv.org/abs/2602.11988)
- arXiv 2606.09090 on "context rot" [SNIP, preliminary]: stale code references in 23.0% of examined CLAUDE.md/AGENTS.md files. — [arXiv](https://arxiv.org/html/2606.09090)
- Agent READMEs study (arXiv 2511.12884, Nov 2025): empirical study of 2,303 context files [SNIP]. — [arXiv](https://arxiv.org/html/2511.12884v1)
- Claude Code docs [FULL, VENDOR]: target under 200 lines per CLAUDE.md; longer files reduce adherence; move partial-codebase instructions to path-scoped `.claude/rules/`; `@imports` organize but do not reduce context cost; contradictory instructions may be picked arbitrarily; review periodically and use the prompt audit (`/doctor prompt-audit`). Keep to facts needed every session; multi-step procedures go to skills. — [Claude Code memory docs](https://code.claude.com/docs/en/memory)
- OpenAI mechanisms (see section 1): index file, doc linters, doc-gardening agent, quality score. — [OpenAI](https://openai.com/index/harness-engineering/)
- Practitioner posts [SNIP, PRACT]: a stale AGENTS.md is trusted fully by the agent; one report of an agent repeating a failed push six weeks later from an outdated line; fixes proposed: edit stale lines instead of appending, point to executable commands instead of prose. — [dev.to: AGENTS.md already stale](https://dev.to/wolfejam/your-agentsmd-is-already-stale-and-your-agent-trusts-it-completely-2nfh); [dev.to: agent keeps docs from going stale](https://dev.to/yureki_lab/how-i-built-an-agent-that-keeps-my-docs-from-going-stale-3pdj)
- O'Reilly ADR piece: rules stated once, cross-referenced; no amendment logs. — [O'Reilly](https://oreilly.com/radar/coding-agents-love-decision-records/)

### Inferences
- Closed taxonomy, hooks blocking unplanned file creation, and "lessons learned that change behavior" (promote a lesson into a lint/test/CLAUDE.md line, then delete the note) have support only by analogy to OpenAI's lint-with-remediation-message approach and the CLAUDE.md size guidance; I found no published evidence on these specifically.
- Redundant summary/notes files are plausibly generated because sessions have no memory of existing docs and no rule against new files; this is my inference, not a sourced finding.

### Gaps
- No multi-month single-team retrospective on doc rot found (search tool said so too); no source on PreToolUse hooks blocking file creation was found; no evidence on "lessons learned" file effectiveness.
- 2606.09090 and 2511.12884 not read in full.

## 5. Session handoff, compaction and built-in memory (Claude Code, late 2026)

### Takeaway
Claude Code has two built-in memory layers (CLAUDE.md written by you; auto memory written by Claude, stored outside the repo) plus local session transcripts; none replaces a repo-tracked status/plan record, and compaction can drop early instructions.

### Cited Findings
- Auto memory: Claude writes learnings itself; scoped per repository and shared across worktrees; first 200 lines or 25KB of `MEMORY.md` load at session start; CLAUDE.md loads every session; AGENTS.md can be read in place of CLAUDE.md; `CLAUDE.local.md` for private per-project preferences. — [Claude Code memory docs](https://code.claude.com/docs/en/memory) [FULL]
- Auto-compaction summary keeps requests and key snippets; early detailed instructions may be lost; "Compact Instructions" section or `/compact focus ...` steers it; auto-compact stops with an error if a single huge output refills context. — [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) [FULL]
- Transcripts are local JSONL under `~/.claude/projects/`; `--continue`/`--resume`/fork exist; checkpoints cover file edits only and are separate from git. — [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) [FULL]
- Handoff contents prescribed by Anthropic harness article: what was done, what is next, how to run/test, git log. — [Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- Third-party claims on compaction threshold (~93%) and community `/memory-save` commands [SNIP, reverse-engineered or community; do not rely]. — [dev.to memory architecture](https://dev.to/oldeucryptoboi/how-claude-code-remembers-and-forgets-the-memory-and-persistence-architecture-55bd)

### Inferences
- Auto memory is machine-local (not in the repo per the docs' own description of storage as per-repository state), so it does not give collaborators or a fresh machine the project state; repo files are the portable record. Where exactly it is stored was not verified.

### Gaps
- No source found on end-of-session ritual conventions beyond Anthropic's; no study on handoff-file formats.
- Whether newer Claude Code versions add a built-in "session summary" feature was not checked.

## 6. Proportionality for a one-person project

### Takeaway
Evidence favors minimal: a short CLAUDE.md (<200 lines), one living status/handoff file, a task list, a few lean ADRs, and an occasional prune. Full spec-kit/BMAD pipelines and many top-level doc files are the parts criticized as overkill.

### Cited Findings
- Measured: context files add >20% cost and do not reliably help; keep only non-standard requirements. — [arXiv 2602.11988](https://arxiv.org/abs/2602.11988)
- Fowler review: spec-kit/Kiro workflows overkill for small and mid-sized work. — [Fowler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- BMAD critics: solo developers get most value from planning, less from the full pipeline [SNIP]. — [Fabrice Monnier](https://fabricemonnier.substack.com/p/think-before-you-build)
- Thoughtworks Radar: prune and consolidate generated Markdown. — [Thoughtworks Radar](https://www.thoughtworks.com/radar/techniques/ai-driven-documentation-sprawl)

### Inferences
- Proportionate: CLAUDE.md index, one STATUS/handoff file overwritten (not appended) each session, a checklist/feature list, lean ADRs for durable decisions, git history as the log, a periodic prune pass.
- Likely overkill for solo: constitution/steering files plus per-feature spec folders, sharded story files, doc-gardening agents and quality-score files (these suit team-scale agent throughput).
- These recommendations are my synthesis; no source tested them on solo projects.

### Gaps
- No source specifically on solo long-lived Claude Code projects over months, including negative retrospectives; only generic practitioner posts surfaced in snippets.
