# Gap Analysis: Useful Ideas From the Original Project Not Yet in the Hackathon Build

> **Source of truth for:** which proven KISS/Pro concepts are missing from the hackathon submission, and where each one should land.
> Sources reviewed: `03 Product 2 - Pro (prototype)` (PRO features doc, Studio Dashboard PRO, popsicle-test.js, studio/ files) and `Keep It Simple Studio - Kit/Master Prompts` (v4 Claude/Codex editions).

## Tier A — High impact, low effort (do before submission)

| # | Idea (from old project) | Why it matters for judges | Where it lands |
|---|---|---|---|
| 1 | **READ_FIRST.md — minimum reading sets per task type** (v3's biggest fix) | This IS the "anti-waste" headline: a small UI tweak shouldn't cost the same context as an architecture review. Directly quantifiable token savings. | CLI `init` template + Foundry agents should consult it before loading knowledge |
| 2 | **PENDING_VERIFICATION.md + verification-debt brake** ("done-but-not-tested is its own state"; stop new features at ~8-10 unverified items) | Unique, research-grade agile insight no other team will have. Easy demo: agent refuses new feature, recommends verification session. | CLI template + scope-check logic + Track 3 Adaptive Card |
| 3 | **Ownership headers on every generated file** ("Source of truth for: X — information lives in exactly one place") | One line per template; makes snapshot-vs-log discipline visible. | All CLI templates |
| 4 | **The Popsicle Test panel** (popsicle-test.js — 5 sliders: shipping? in control? time respected? compute well spent? proud?) | Already written, drop-in JS, localStorage. PROJECT_PLAN promises a "Popsicle Index" and the hackathon dashboard doesn't have it. | `dashboard/index.html` |
| 5 | **Context Weight & ROI panel** (estimate token cost of each task's reading set *before* spending, $/1M input) | The product's #1 hook per the PRO research: "planning tool, not an accountant." Free token trackers measure past spend; this is pre-spend. | Dashboard + `kiss status` token estimate |

## Tier B — Medium effort, strong demo value

| # | Idea | Where it lands |
|---|---|---|
| 6 | **Bloat/efficiency warnings** (PROJECT_STATE over word limit, ITERATION_LOG over entry count, "Now" over task count) | Dashboard + `kiss status` |
| 7 | **Context-health / "buried instructions" check** — flag critical rules buried mid-file (backed by "lost in the middle" / Context Rot research) | Perfect job for a 4th Foundry agent (Track 2) — turns published research into a reasoning agent |
| 8 | **Auto-drafted retrospectives** every ~5 iterations, drafted from ITERATION_LOG (never a blank template) | CLI `kiss retro` command or Foundry Manager Insights agent |
| 9 | **Scope-check should parse PRODUCT_VISION.md tiers**, not hardcoded keyword lists (current `checkScope()` uses static keywords) | `projectManager.ts` |
| 10 | **Memo capture** — inbox for loose ideas, promotable to task or decision | Dashboard panel or `kiss memo "<idea>"` |

## Tier C — Capture in docs/judges brief, don't build

- **Intake calibration sliders** (Speed vs Polish, Scope vs Simplicity, Cost vs Quality, Hands-off vs Hands-on, Fast vs Safe) feeding DEFINITION_OF_DONE.md and RISK_POLICY.md.
- **DEFINITION_OF_DONE.md and COMPLIANCE.md** as optional generated files (compliance slot: ask at intake if project touches user data/payments/regulated content).
- **Workflow-mode recommendation** (Verification-first / Stabilization / Launch-readiness / Build-Measure-Learn / Focused sprint) — agent names the right mode before working.
- **Product Owner discipline**: client owns WHAT, agent owns WHY; challenge weak requests once with risk + smaller option; silence is never approval. (Partially in RISK_POLICY template already.)
- **Agent-agnostic core + thin per-agent adapter** (CLAUDE.md vs AGENTS.md entry file) — one paragraph in the judges brief shows the methodology isn't Copilot-locked while the integrations are.
- **Studio upgrade path** — detect old/informal project notes and offer to convert to the file set (relocate, never delete).
- **Market positioning for the brief**: token trackers (ccusage etc.) are free commodities measuring *past* spend; KISS estimates *pre-spend* reading cost and ties it to ROI for non-technical builders. That's the defensible niche.

## Already captured (no action)

Scope tiers + parking in DECISIONS.md, decision logging with why/revisit, session memory via PROJECT_STATE.md, AGENT_CONTEXT.md handoffs, BRAND_VOICE.md extraction, 4-column board, iteration log, risk-policy stop conditions.

## Decision log (hackathon-week scope calls)

- **D-H01** | 2026-06-11 | Track 1 demo = D&D campaign generator (survey = KISS intake; Track 2 governs scope live; Azure image gen for art) | Why: more creative than copy generation, showcases methodology on a fun project | Status: ACCEPTED
- **D-H02** | 2026-06-11 | Adopt Accept/Warn/Block decision triad in Assessment Agent | Why: richer semantics than binary block | Status: ACCEPTED
- **D-H03** | 2026-06-11 | Interactive AI video | Why parked: high risk, no rubric payoff, competes with submission requirements | Status: PARKED (Tier 2) | Revisit: all tracks submitted with >1 day to spare
- **D-H04** | 2026-06-11 | Provider abstraction, AES encryption, Power Automate hooks | Why parked: product roadmap, not hackathon scope | Status: PARKED (Tier 3)
- **D-H05** | 2026-06-11 | Governed asset generation: ASSET_POLICY.md + per-asset ACCEPT/WARN/BLOCK risk check + cost-before-spend estimate + generation traces + asset verification queue | Why: applies KISS methodology to creative AI output; strong Reliability & Safety scoring; unifies all three tracks | Status: ACCEPTED (Track 1) | Note: policy covers AI video; video generation itself stays parked per D-H03
