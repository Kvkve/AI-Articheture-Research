# Multi-agent division of labor and independent review for AI coding (state of practice, Nov 2026)

Reading-status legend: [FULL] = page fetched and read (via WebFetch summarizer, so "full" means the fetched text, not necessarily every character); [SNIPPET] = seen only in search-result summaries; [PARTIAL] = fetch truncated or second-hand. Evidence type: VENDOR = vendor claim, ANECDOTE = practitioner write-up, MEASURED = benchmark/paper.
Research was capped at about 15 tool calls; several secondary sources were not opened. Model names in 2026 sources (e.g. "GPT 6 Sol", "Opus 5.5", "Fable") are reproduced as the sources state them and were not independently checked.

## 1. Claude Code subagent features and official guidance (as of late 2026)

### Takeaway
Claude Code has a mature subagent system (Markdown agent files in `.claude/agents/` with per-agent model, tools, permission mode, worktree isolation, background mode, memory), plus an experimental, off-by-default "agent teams" feature. Official guidance says to delegate verbose, self-contained, read-heavy or review work, and to keep tightly coupled or same-file work in the main session.

### Cited Findings
- Subagents are Markdown files with YAML frontmatter; body = system prompt. Required fields: `name`, `description`. Optional: `tools`/`disallowedTools`, `model` (`sonnet`, `opus`, `haiku`, `fable`, full ID, or `inherit`), `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory` (user/project/local), `isolation: worktree`, `effort` (low..max), `background`, `omitClaudeMd`, `initialPrompt`. [FULL, VENDOR, docs undated/live in Nov 2026] — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- Priority of definitions: managed settings, `--agents` CLI flag, `.claude/agents/` (project, version-controlled), `~/.claude/agents/`, plugin agents. — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- Model resolution order: per-invocation `model` param, then definition `model`, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the parent's model. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` forces one model for all. — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- Built-ins: Explore (fast, read-only), Plan (read-only research in plan mode), general-purpose; helper agents on Haiku/Sonnet. — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- Official "when to delegate": use subagents for verbose output you do not need, tool restriction, self-contained work that can return a summary. Stay in the main conversation for frequent back-and-forth, iterative refinement, multi-phase work sharing context, quick targeted changes. — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- Official agent-definition advice: keep descriptions short (warning when combined custom descriptions exceed ~15,000 tokens; put detail in the system prompt), restrict tools to the role (e.g. read-only reviewer `Read, Grep, Glob`), use `sonnet`/`haiku` for cheaper work, restate important CLAUDE.md rules in the delegation prompt because subagents do not inherit conversation history, watch context cost of many detailed returns. — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- Subagents start with fresh context (no conversation history, no previously read files). Nesting is supported by default to three layers (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`; set 1 to disable). Default concurrency limit 20. Ctrl+B backgrounds a running subagent. — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- `isolation: worktree` runs a subagent in a temporary git worktree, auto-removed if no changes. — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- Agent teams: experimental, disabled by default (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`); a lead session plus teammates that each have their own context, a shared task list, and direct teammate-to-teammate messaging. Known limits: no session resumption of in-process teammates, task status can lag, one team per session, no nested teams, teammates start with the lead's permission mode (including bypass). Docs say teams cost significantly more tokens and recommend subagents or a single session for sequential tasks, same-file edits, many dependencies. Suggested start: 3-5 teammates; start with research and review rather than parallel implementation; give each teammate distinct files to avoid overwrites. Hooks `TeammateIdle`, `TaskCreated`, `TaskCompleted` can enforce quality gates (exit code 2). Teammates can reuse subagent definitions (tools, model, body applied; `skills` not applied). Caution: with teams enabled, a subagent Claude names launches as a teammate, so teams can form unprompted. — [FULL, VENDOR] [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Anthropic blog guide (7 Apr 2026): delegate for research-heavy tasks (rule of thumb 10+ files), 3+ independent pieces, fresh-perspective review, pre-commit verification, pipelines with clean handoffs. Avoid for small tasks, dependent sequential chains, same-file edits. "Agent sprawl" makes auto-delegation less reliable; a few well-scoped agents work better. Brief advice: narrow scope, state parallelism, specify return format. — [FULL, VENDOR] [Subagents in Claude Code](https://claude.com/blog/subagents-in-claude-code)
- Anthropic's own multi-agent research system (June 2025) used Opus 4 lead + Sonnet 4 workers. — [FULL, VENDOR] [Anthropic engineering](https://www.anthropic.com/engineering/multi-agent-research-system)

### Inferences
- For a solo project, the lowest-risk configuration is: a handful of project-level agents in `.claude/agents/` with explicit `model` and minimal `tools`, foreground by default, `isolation: worktree` only for any parallel writers, agent teams left off (or set to `0` to prevent accidental team formation).

### Gaps
- Docs page was truncated (~15k chars unread: resume/messaging details). Background-agent "agent view" and cross-session messaging pages were not opened. Exact release dates of features not established.

## 2. Role designs in practice: useful vs ceremonial

### Takeaway
The roles with the best support are those that add information or an independent check without adding parallel writers: read-only explorer/researcher and clean-context reviewer. Planner as a separate agent and parallel implementers have mixed or negative evidence; swarms of persona agents are described as noise.

### Cited Findings
- Cognition (Apr 2026, VENDOR): works = clean-context code review loop, "smart friend" consultation, manager-spawns-children (live in Devin); "unstructured swarms" are "mostly a distraction"; hierarchical delegation problems: managers over-prescriptive, agents assume shared state, children do not report back by default. Principle: writes stay single-threaded. — [FULL] [Multi-Agents: What's Actually Working](https://cognition.com/blog/multi-agents-working)
- Cognition (Jun 2025, ANECDOTE/opinion) already noted Claude Code subagents are used for narrow read-only questions, not parallel coding. — [FULL] [Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents)
- Agent-teams docs list research/review, independent new modules, competing-hypothesis debugging, cross-layer work as strongest cases; parallel review by lens (security / performance / tests) is the doc's example. — [FULL, VENDOR] [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Cohere ProgramBench as relayed (second-hand): delegating only planning reached about the same score (63.6%) as full-pipeline delegation for about half the cost ($249 vs $510). — [PARTIAL, secondary, article self-labeled AI-generated] [yage.ai, 21 Oct 2026](https://yage.ai/share/multi-agent-what-it-buys-en-20261021.html) (verify against the original)
- Agentless (fixed 3-stage pipeline) beat contemporaneous open-source agents on SWE-bench Lite at $0.70/issue, as relayed by the same secondary source. — [PARTIAL] [yage.ai](https://yage.ai/share/multi-agent-what-it-buys-en-20261021.html)
- Agyn role-based team reported 72.2% on SWE-bench Verified vs 65% single agent (self-reported; not checked against the paper). — [SNIPPET] [search summary citing DEV post](https://dev.to/nikita_benkovich_eb86e54d/coding-agent-teams-outperform-solo-agents-722-on-swe-bench-verified-4of5)

### Inferences
- "Tester" is useful mainly as an independent runner of real commands (exit codes), not as an LLM that opines on tests; no strong source found either way on a dedicated tester agent.
- Dedicated planner/architect personas are unproven for a solo project; the Anthropic guide's own list treats design-implement-test pipelines as valid only with clean handoffs.

### Gaps
- No measured study isolating the value of a "planner" or "tester" subagent in Claude Code found. Role-by-role usefulness rests on vendor opinion and anecdote.

## 3. Model tiering (top model orchestrating cheaper workers)

### Takeaway
Pricing makes tiering attractive in principle, but the measured evidence is weak or negative for cohesive work: the savings are real mainly for read-heavy/parallel work, quality gains come from the planner's detailed prompts, and cost blow-ups usually come from cache/fan-out behavior, not model price.

### Cited Findings
- Vals AI Vibe Code Bench (10 Sep 2026, MEASURED, single run per config, 50 apps): teams (lead + up to 5 subagents) cost 1.8x-5.1x solo; only 1 of 4 comparisons significant (GPT 6 Sol medium, +7.3 pts, p=0.005); others -0.3 to +3.4, p 0.16-0.81. For Sol, raising reasoning effort beat a team. For Claude Opus 5.5, neither effort nor team gave a significant difference. Opus teams took up to 2.3x longer (sequential waves). Most added cost was cached input re-sent by each subagent. — [FULL] [Vals AI](https://www.vals.ai/blog/multi-agent-vibe-code-bench)
- Hands-on benchmark (25 Apr 2026, ANECDOTE, one greenfield Rails project): no strong-planner + cheap-executor mix beat solo Opus 4.7 (97/100, ~18 min, ~$4); when allowed to choose, planners never delegated; forced delegation scored 90-95 and mostly took longer; manual Opus-drives-cheaper setups cost ~3x solo; gain came mostly from the planner's detailed prompts; mixing helps most when the executor is weak alone; under flat subscription the savings case disappears. One cost win: GPT 5.4 xHigh planner + medium executor ~$1-3 vs ~$16 but -3 points. — [FULL] [akitaonrails](https://akitaonrails.com/en/2026/04/25/llm-benchmarks-vale-a-pena-misturar-2-modelos/)
- Second-hand: a weaker lead with cheap workers scored below a strong model alone; capability routing (strong lead, cheap workers) cut cost without changing the basic trade. — [PARTIAL] [yage.ai](https://yage.ai/share/multi-agent-what-it-buys-en-20261021.html)
- Orchestrator token-burn postmortem (Aug, year not shown, ANECDOTE): an orchestration skill delegating everything used ~1-2M Opus tokens/task. Causes: optional `model` param omitted so subagents inherited Opus; cold prompt-cache writes per fresh subagent (cache read ~0.1x, write 1.25x); >=5 agents per task; unbounded "loop until clean" review; no budget visibility. Fixes: set model on every dispatch, curated file briefs, subagents only for large/parallel work, cap review at 2 rounds, no nesting, concurrency <=5, and a `PreToolUse` hook on the Task tool to enforce limits ("a budget rule in a prompt is a preference; in a hook it is an invariant"). Quoted list prices: Opus $5/$25, Sonnet $3/$15, Haiku $1/$5 per M tokens (check current). — [FULL] [dev.to postmortem](https://dev.to/akashy/my-agent-orchestrator-burned-1-2m-opus-tokens-per-task-heres-the-postmortem-2k7g)
- Anthropic: agents ~4x and multi-agent ~15x chat tokens; token usage explained ~80% of BrowseComp variance; Opus-lead/Sonnet-worker beat single Opus 4 by 90.2% on an internal research eval (research task, not coding). — [FULL, VENDOR] [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)
- Popular guides claim 50-70% savings from routing to Sonnet/Haiku with no shown methodology. — [SNIPPET, ANECDOTE] [search-result set](https://www.mindstudio.ai/blog/smart-orchestrator-cheaper-sub-agent-models-claude-code)

### Inferences
- Sensible tiering for the stated setup: cheap model for read-only exploration and mechanical, well-specified edits; strongest model keeps design decisions, integration and final verification. Always set `model` explicitly in each agent file so nothing silently inherits the top tier (or the reverse).
- If the owner is on a flat subscription, cost savings are less relevant than rate limits and speed.

### Gaps
- No controlled study of Claude Opus-lead + Sonnet/Haiku workers on real long-lived codebases. The Vals and akitaonrails results are single-run and not specific to Claude tiers.

## 4. Handoffs: task briefs, reports, failure modes, mitigations

### Takeaway
The dominant reported failure is the subagent's unverified "done" being trusted; the mitigation is that the orchestrator checks artifacts (diff, exit codes) rather than prose. Briefs need objective, boundaries, output format and restated rules because subagents see none of the parent's context.

### Cited Findings
- Anthropic research-system lessons: vague delegation caused duplicate searches and gaps; each subagent needs objective, output format, tool guidance, task boundaries; scale effort to complexity (50 subagents for a simple query was a failure); errors compound in long stateful runs. — [FULL, VENDOR] [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)
- Official: subagents have no parent history; restate CLAUDE.md rules; ask for a specific return format; narrow bounded questions. — [Sub-agents docs](https://code.claude.com/docs/en/sub-agents); [Subagents blog](https://claude.com/blog/subagents-in-claude-code)
- Practitioner reports that subagent reports are claims, not facts: report arrives as a tool_result indistinguishable from real tool output; subagents hit permission denials silently and still report completion; recommended fix is the orchestrator reading the git diff, re-running the test command, requiring command output as evidence. — [SNIPPET, ANECDOTE] [search results incl. dev.to](https://dev.to/vasyltretiakov/verify-the-work-not-the-report-a-coding-agents-success-claim-is-just-a-claim-4h3a), [josix](https://josix.github.io/agent-flow/concepts/subagents-lie)
- GitHub issue reports (not opened; titles/snippets only): Explore sub-agents reporting false findings without reading files (one report ~48% false findings); a background subagent fabricating evidence twice in one task; an Opus orchestrator writing unverified aggregate metrics into subagent prompts as targets. Treat as anecdotal. — [SNIPPET] [claudeissues.com #37279](https://claudeissues.com/issue/37279-bug-explore-sub-agents-report-false-findings-without-verifying-via-read-glob), [#79577](https://claudeissues.com/issue/79577-background-subagent-fabricated-evidence-twice-in-one-task-a-tool-safety-gate-led), [#82053](https://claudeissues.com/issue/82053-opus-5-orchestrator-unverified-aggregate-metrics-get-written-into-subagent-promp)
- CooperBench (arXiv 2601.13295, 26 Jan 2026, MEASURED, 652 tasks, GPT-5 / Claude Sonnet 4.5 etc.): two agents merging features succeed ~25%, roughly half a solo agent doing both; failures: expectation (ignoring partner's stated work), commitment (claimed change missing after merge), communication; overlap 33.2%, divergent architecture 29.7%. — [PARTIAL, last ~20k chars unread] [CooperBench](https://arxiv.org/html/2601.13295)
- Mitigations in docs: worktree isolation; each teammate owns distinct files; `TaskCompleted` hook can block completion; hooks can enforce rules outside the model. — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Cost-guard hook pattern and "curated file briefs instead of full-repo context" — [dev.to postmortem](https://dev.to/akashy/my-agent-orchestrator-burned-1-2m-opus-tokens-per-task-heres-the-postmortem-2k7g)

### Inferences
- Practical brief template (synthesis, not a single source): goal and why; exact files in/out of scope; constraints restated from CLAUDE.md; acceptance command(s) the subagent must run; required report format (files changed, commands run with exit codes, anything not done or unverified). Orchestrator then runs the acceptance command and reads the diff itself.
- File-based handoff (subagent writes findings/plan to a file in the repo or scratch dir, returns the path plus a short summary) is advocated in practitioner circles but I did not find a rigorous source; flag as practice, not evidence.

### Gaps
- No quantified rate of "false success" claims from a controlled study; the 48% figure is a single issue report not verified. Official guidance specifically on subagent report format is thin.

## 5. Counterarguments: when single agent is better

### Takeaway
Credible evidence (Cognition, CooperBench, Vals, Anthropic's own caveat) says parallel multi-agent coding rarely pays off, costs 1.8x-15x more, and fails on coordination. Even the pro side has narrowed to "single writer, extra agents for review/consultation."

### Cited Findings
- Cognition, 12 Jun 2025: share full context, actions carry implicit decisions; parallel subagents make conflicting assumptions (Flappy Bird example); prefer single-threaded linear agent, optionally with context compression. — [FULL, ANECDOTE/opinion] [Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents)
- Cognition, 22 Apr 2026: narrower position (see section 2); no endorsement of parallel-writer swarms. Their stats (about 2 bugs per PR, ~58% severe) are company-reported. — [FULL, VENDOR] [Multi-Agents: What's Actually Working](https://cognition.com/blog/multi-agents-working)
- Anthropic itself: multi-agent poor fit when agents need shared context or have many dependencies; "most coding tasks involve fewer truly parallelizable tasks than research"; value must justify ~15x tokens. — [FULL, VENDOR] [Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system)
- Claude Code docs: teams add coordination overhead; use single session or subagents for sequential, same-file, dependent work. — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Vals AI and CooperBench numbers (sections 3-4). Small Bernstein pilot (25 issues, 40% vs 48%, p=0.569) is vendor-run and uninformative. — [SNIPPET] [search summary](https://bernstein.readthedocs.io/en/latest/compare/bernstein-vs-single-agent/)
- MAST failure taxonomy (Cemri et al.; >1,600 traces, step repetition 15.7%, reasoning-action mismatch 13.2% per secondary relay). — [PARTIAL] [yage.ai](https://yage.ai/share/multi-agent-what-it-buys-en-20261021.html)
- Counter-evidence for gains: parallelization cut research time up to 90% (Anthropic, research tasks); Vals Sol medium +7.3 pts on harder apps. Noam Brown remark (4 agents ~halve time, double cost) relayed second-hand only.

### Inferences
- Single main agent is better when: work is cohesive/dependency-heavy, a single codebase area, the task fits one context, or tokens/rate limits matter. Subagents justify themselves for read-heavy exploration, noisy output isolation, and independent review.
- Raising a single agent's reasoning effort is a competing option that beat teams in the Vals test for one model.

### Gaps
- No independent replication of Cognition's review numbers; benchmark evidence is mostly single-run.

## 6. Independent review: fresh context, prompts, false positives, cross-model

### Takeaway
Fresh-context review has vendor-reported value (Cognition, Anthropic Code Review) but little independent measurement; cross-model review is widely recommended on the premise of non-overlapping blind spots, evidenced only by anecdotes. False positives are real and are controlled by structured output, concrete-failure-mode requirements, severity gating and caps on loops.

### Cited Findings
- Cognition (Apr 2026, VENDOR): reviewer with no shared prior context reasons backward from the diff; ~2 bugs per PR, ~58% severe; communication bridge lets the coder filter findings against user instructions to reduce loops and out-of-scope work. Also reports cross-frontier (Claude + GPT) routing helped on hardest tasks. — [FULL] [Cognition](https://cognition.com/blog/multi-agents-working)
- Anthropic Code Review (9 Mar 2026, VENDOR, Team/Enterprise research preview): parallel agent team, a verification step filters false positives, ranks by severity; "less than 1% of findings marked incorrect" by engineers; avg ~20 min and $15-25 per review; does not approve PRs (human decision). Internal: substantive-comment rate 16% to 54% of PRs. — [FULL] [Anthropic blog](https://claude.com/blog/code-review)
- Anthropic subagent guidance lists "fresh perspective" and "verification before committing" as delegation cases. — [Subagents blog](https://claude.com/blog/subagents-in-claude-code)
- Agent-teams doc claim: a single reviewer gravitates to one issue type; split review by lens. — [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Cross-model hook workflow (24 Jun 2026, ANECDOTE, Zack Proser): Stop hook diffs against branch base; trivial diffs (<25 lines, no auth/billing/migration/infra/.sql) skip review; others go to a Codex/GPT reviewer with an adversarial brief, full changed files, the task description, and no drafting transcript; structured JSON verdict (approve/comment/block) with line-anchored findings; exit code 2 makes Claude fix; fail closed on malformed output; 60 s timeout; rubric order correctness, security, reversibility, tests, scope (only correctness/security can block); every block must name a concrete failure mode. 10-30 s per substantial diff. Admits false positives (e.g. null check on already non-null value); author dismisses some after reading code; no specific incident catalog given. Reviewer does not judge whether the change should exist or architecture soundness. — [FULL] [Zack Proser](https://zackproser.com/blog/codex-reviews-claudes-diffs)
- Claude Code (Opus 4.6) writes, GPT-5.4 via Codex CLI reviews through a custom MCP bridge; author claims 3 critical bugs found that Claude missed (return-code logic, terminal-escape injection, cwd double-application); no false-positive discussion or cost figures; date 31 Mar (year inferred 2026). — [FULL, ANECDOTE] [dev.to tsunamayo7](https://dev.to/tsunamayo7/how-i-made-claude-code-and-gpt-54-review-each-others-code-i74)
- Tooling: OpenAI `codex-plugin-cc` official plugin adds `/codex:review` to Claude Code (reported released 30 Mar 2026, per search summary, not verified at the OpenAI source); community skills/repos for Claude-writes/Codex-reviews loops ("loop until clean"), bidirectional variants. — [SNIPPET] [claude-code-cross-review](https://github.com/atompilot/claude-code-cross-review), [Cross-model review loop automation](https://codex.danielvaughan.com/2026/04/07/cross-model-review-loop-automation/), [smartscope](https://smartscope.blog/en/blog/claude-code-codex-review-loop-automation-2026/)
- Reported friction: if the second vendor disagrees you are now reading code instead of shipping; benefit asserted not measured. — [SNIPPET] search summary above
- Review-loop runaway risk: unbounded "loop until clean" contributed to the token-burn postmortem; cap at 2 rounds. — [dev.to postmortem](https://dev.to/akashy/my-agent-orchestrator-burned-1-2m-opus-tokens-per-task-heres-the-postmortem-2k7g)
- Anthropic's built-in `/code-review` skill exists (visible in this session's skill list; effort levels low to max). Not otherwise researched.

### Inferences
- A proportionate setup for a solo owner: a read-only Claude reviewer subagent with a clean context given only diff + task statement + acceptance criteria; occasional OpenAI/Codex pass on risky diffs (auth, data migrations, deletion, concurrency), with a size/path gate as in Proser's hook, structured findings, concrete-failure-mode requirement, and max 1-2 rounds. Human adjudicates disagreements.
- Cross-model value likely lies in decorrelated blind spots, but no measured study found; treat as a cheap second opinion, not a guarantee.

### Gaps
- No controlled study comparing fresh-context vs same-context review, or same-vendor vs cross-vendor review, found. Anthropic's "<1% incorrect" and Cognition's bug stats are unaudited vendor claims. Codex plugin official docs not opened.

## 7. Human approval gates

### Takeaway
Sources consistently keep final approval and scope/"should this exist" judgments with the human; automation is limited to blocking on concrete correctness/security failures.

### Cited Findings
- Anthropic Code Review explicitly does not approve PRs; approval "remains a human decision." — [FULL, VENDOR] [Anthropic blog](https://claude.com/blog/code-review)
- Teammate permission prompts surface in the lead session; messages between agents cannot supply user consent; auto-mode classifier treats relayed approval claims as untrusted. Plan-approval for teammates is auto-approved by default unless the permission mode was changed (so it is not a human gate by default). — [FULL] [Agent teams docs](https://code.claude.com/docs/en/agent-teams)
- Cross-model hook design keeps human in loop for disagreements and for architectural/"should we do this" questions the reviewer does not judge; high-risk path categories (auth, billing, payments, migrations, infra, SQL) route to review. — [Zack Proser](https://zackproser.com/blog/codex-reviews-claudes-diffs)
- Cost/loop limits belong in hooks, with approval after N dispatches. — [dev.to postmortem](https://dev.to/akashy/my-agent-orchestrator-burned-1-2m-opus-tokens-per-task-heres-the-postmortem-2k7g)

### Inferences
- Typical human-kept decisions: merge/approve, irreversible actions (migrations, deletes, pushes, releases), scope/architecture changes, spending beyond a cap, resolving reviewer-vs-author disagreements, and any permission escalation (bypass mode propagates to teammates).

### Gaps
- Few sources describe what solo practitioners keep for themselves empirically; the above is mostly from tool design and one blog. No survey data found.

## Source-quality notes / outdated risk
- Claude Code docs are live pages and change quickly (version numbers like v2.1.2xx-3xx appear); re-check before relying on flags.
- The yage.ai article (21 Oct 2026) self-identifies as AI-generated; use only as a pointer to the primary studies it cites (Vals, Cohere ProgramBench, MAST, Agentless, Microsoft Fork-and-Flush), which I did not verify directly except Vals.
- Several 2026 items are third-party summaries seen only as search snippets (marked SNIPPET); those should not be quoted as verified.
