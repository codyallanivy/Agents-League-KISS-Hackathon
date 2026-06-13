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
- **Reliability:** the demo cannot dead-end — every tier degrades gracefully

## Rubric mapping
- **Accuracy & Relevance** — five-agent enterprise learning/certification system per the scenario; all three IQ layers integrated (local modules matching each product's contract; model tier on real Azure Foundry)
- **Reasoning & Multi-step** — planner-executor orchestration + critic/verifier that fails uncited answers; prerequisite-graph and threshold reasoning from the Fabric IQ ontology
- **Creativity** — the certification's practical exam IS live scope governance; governed asset generation (policy manual, cost-before-spend, verification queue); docs→vision-board visualization
- **UX & Presentation** — three-view Command Center; onboard any folder in two clicks; adaptive intake survey; one-click start.bat
- **Reliability & Safety** — synthetic data only; Accept/Warn/Block with human override; verification-debt brake; budget caps; content/rights rules in ASSET_POLICY.md; offline-first privacy

## Differentiator
Most teams will demo agents that *answer*. KISS Studio demos agents that **refuse correctly** — and prove why, with citations, every time. The methodology is agent-agnostic; the integrations are Microsoft-native; the system was built solo in 10 days *using its own rules* (see GAP_ANALYSIS.md's D-H01…D-H13 decision log — every scope call this week is recorded there).
