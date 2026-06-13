# Judges Brief — KISS Studio

## Problem
AI assistants lose project context between sessions, accept out-of-scope work by default, and burn compute invisibly. Existing token trackers measure *past* spend, for developers, in terminals. Non-technical builders get nothing.

## Solution
KISS Studio makes plain Markdown the durable memory of a project, then wraps every AI action in governance: ACCEPT/WARN/BLOCK scope decisions grounded in the project's own PRODUCT_VISION, context cost estimated **before** spending, done-but-unverified work tracked as first-class debt, and every reasoning step cited and traced to queryable JSONL.

## Proof (everything below is demoable + rerunnable)
- **Scope governance:** "build the merch store" → Tier 3 → BLOCK → parked with revisit trigger (rule R-4), grounded in the project's files
- **Evaluations:** 10-case eval suite (from our Cold-Run Test Kit methodology) — 10/10 offline, rerunnable per model tier (`evals.py`, reports stamped with model)
- **Observability:** every prompt/citation/verdict in JSONL traces; one Data Explorer query reaches 6 sources including each IQ layer
- **Model ladder:** Foundry (gpt-4o) → Ollama (local open-weight) → deterministic offline; live side-by-side Compare with latency; preference capture in DPO-pair format
- **Project-memory isolation:** retrieval is scoped to the *active* project plus shared method knowledge, so one project's context can never contaminate another project's reasoning. The creative/intake layer is fully domain-neutral; an optional Fantasy Campaign template is isolated (never discovered, never indexed) and influences nothing else.
- **Reference-grounded creation:** the intake studio searches the project's own references (intake answers, vision tiers, related knowledge) *before* it writes the creation document or generates any gallery asset — assets reflect what the project actually needs, not a fixed template.
- **Reliability:** the demo cannot dead-end — every tier degrades gracefully

## Rubric mapping
- **Accuracy & Relevance** — five-agent enterprise learning/certification system per the scenario; all three IQ layers integrated (local modules matching each product's contract; model tier on real Azure Foundry)
- **Reasoning & Multi-step** — planner-executor orchestration + critic/verifier that fails uncited answers; prerequisite-graph and threshold reasoning from the Fabric IQ ontology
- **Creativity** — the certification's practical exam IS live scope governance; governed asset generation (policy manual, cost-before-spend, verification queue); docs→vision-board visualization
- **UX & Presentation** — three-view Command Center; onboard any folder in two clicks; adaptive intake survey; one-click start.bat
- **Reliability & Safety** — synthetic data only; Accept/Warn/Block with human override; verification-debt brake; budget caps; content/rights rules in ASSET_POLICY.md; offline-first privacy

## Differentiator
Most teams will demo agents that *answer*. KISS Studio demos agents that **refuse correctly** — and prove why, with citations, every time. The methodology is agent-agnostic; the integrations are Microsoft-native; the system was built solo in 10 days *using its own rules* (see GAP_ANALYSIS.md's D-H01…D-H13 decision log — every scope call this week is recorded there).

## How to run (Windows, Python only)
1. `start.bat` → **[1] Command Center** opens `http://localhost:8765`.
2. On the home screen click **▶ Load Judge Demo** (prefills the inputs), then walk the **Demo flow** strip: Builder Studio → Scope Gate → Board/Health/Traces → Vision Board → M365 Governance view.
3. **🧱 Builder Studio** tab (or `start.bat` → [6]) for the visual builder; **← Command Center** returns.
4. Evals: `cd foundry-track2 && python evals.py` (10/10 offline). Optional cloud upgrade: `setup-azure.ps1` provisions a real Azure Foundry gpt-4o deployment; with `foundry-track2/.env` set, the dashboard's model badge flips to **FOUNDRY**.
5. Optional, isolated example: `start.bat` → **[3] Fantasy Campaign template** (writes only into `creative-track1/fantasy-template/`; affects nothing else).

## What is real vs simulated
- **Real:** the reasoning engine, planner-executor orchestration, the cited critic, the three IQ modules (local implementations matching each product's contract), the eval suite, JSONL tracing, the Asset Governor, the Command Center, and Builder Studio. With Azure configured, the model tier is a **real** Foundry gpt-4o deployment.
- **Simulated (clearly labeled "mock"):** only the **M365 / Teams governance view** (`m365-track3/mock-ui`) — and even that renders from real Track 2 outputs plus synthetic learner data. All learners, work signals, companies, and documents are **synthetic** (no real persons or tenant data).

## Where Azure & Microsoft IQ fit
- **Foundry IQ** → grounded knowledge base over approved sources; every retrieval returns citations; the critic fails uncited answers (`foundry-track2/iq/foundry_iq.py`). Model tier maps to an Azure Foundry gpt-4o deployment.
- **Fabric IQ** → ontology of certifications/roles/skills/scope tiers + business rules R-1…R-5 that agents reason with (`data/ontology.json` + `iq/fabric_iq.py`).
- **Work IQ** → synthetic work-pattern signals (meeting load, focus hours) driving scheduling and capacity-risk flags (`iq/work_iq.py`).
- **M365** → a Copilot declarative agent + Adaptive Cards surface the engine's real decisions for managers (`m365-track3/`).

## Known limitations
- Offline tier uses deterministic templates and SVG assets (intentional, so the demo never dead-ends); richest prose/art needs Ollama or Azure Foundry.
- The M365/Teams surface is a local mock; live Microsoft Graph sync is parked (see DECISIONS log).
- Foundry IQ retrieval is keyword-overlap (demo-grade), not a hosted vector index; the hosted mapping is documented but not run locally.
- Single-user local server (stdlib `http.server`); not hardened for multi-tenant deployment.
