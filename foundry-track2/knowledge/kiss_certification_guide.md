# KISS AI-Collaboration Certification Guide (Synthetic)

> **Source of truth for:** the internal certification programme that teaches teams to collaborate with AI agents using the Keep It Simple Studio (KISS) methodology.
> **Note:** This document is synthetic demonstration content for the Agents League hackathon. Company, programme, and all data are fictional.

## Programme Overview

Pizza Shop Co. requires every employee who works with AI coding agents to complete role-appropriate KISS certifications. The programme exists because AI assistants are powerful but forgetful: without method, teams lose project context between sessions, scope creep derails sprints, and tokens are wasted on out-of-scope work.

## Certification Levels

### KISS-101 — Foundations: AI-Collaboration Basics
- **Skills:** Project memory files, snapshot-vs-log discipline, decision logging
- **Recommended study:** 8 hours
- **Pass threshold:** 75% practice score
- **Core content:** The seven project memory files (PROJECT_STATE, DECISIONS, RISK_POLICY, TODO, ITERATION_LOG, AGENT_CONTEXT, PRODUCT_VISION). PROJECT_STATE.md is a snapshot of current truth; ITERATION_LOG.md is the dated history. Never let the snapshot become a changelog. Every material decision is logged with an ID (D-XXX), date, reason, and revisit trigger.

### KISS-201 — Practitioner: Scope Discipline & Token ROI
- **Skills:** Tier classification, scope-creep stop conditions, reading-set cost estimation, verification-debt management
- **Recommended study:** 14 hours
- **Pass threshold:** 75% practice score
- **Prerequisite:** KISS-101
- **Core content:** Features are classified into tiers. Tier 1 is current launch scope: build it. Tier 2 is post-launch and Tier 3 is vision-only: capture them in DECISIONS.md with a revisit trigger — never build them during an active sprint. The default answer to "should we also build X?" is "capture it, don't build it." Done-but-not-tested work lives in PENDING_VERIFICATION.md; when more than ~2 iterations of unverified work accumulates, stop building and verify. READ_FIRST.md defines the minimum file reading set per task type so a small tweak never costs the context of a full architecture review.

### KISS-301 — Coach: Multi-Agent Governance
- **Skills:** Agent handoff context, risk-policy authoring, retrospective facilitation, manager insight reporting
- **Recommended study:** 20 hours
- **Pass threshold:** 80% practice score
- **Prerequisite:** KISS-201
- **Core content:** AGENT_CONTEXT.md records who worked, what they did, assumptions, and open questions so multi-agent handoffs survive session boundaries. RISK_POLICY.md defines what agents may do alone versus what needs the Product Owner. Retrospectives are auto-drafted from ITERATION_LOG.md every ~5 iterations. The client owns WHAT; the agent owns WHY — silence is never approval.

## Role Requirements

- Developer: KISS-101, KISS-201
- Project Manager: KISS-101, KISS-201, KISS-301
- Designer: KISS-101

## Recommended Study Pattern

- 1–2 hours of focused study daily, scheduled inside focus hours (never over meeting-heavy periods)
- Weekly practice assessment checkpoints
- Target the pass threshold on practice scores before sitting the exam
- Learners with more than 20 meeting hours per week show lower study completion; managers should protect focus time

## Practical Exam Format

The applied portion of KISS-201 and KISS-301 uses a live project simulation (the synthetic "pizza-shop" project). Candidates receive incoming feature requests and must: classify the tier with reasoning, cite PRODUCT_VISION.md, choose the correct action (proceed or park), and draft the DECISIONS.md entry.
