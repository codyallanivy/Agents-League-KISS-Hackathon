# Risk Policy — Pizza Shop MVP

**Client Authority:** Cody (final decision maker). Agent recommends; Cody decides.

## The Scope-Creep Stop Condition (LOCKED)

**STOP and ask Cody before doing any of:**
- Building Tier 2 (analytics, team features, delivery tracking) — Tier 1 must ship first
- Adding features not in agile/PRODUCT_VISION.md "In scope for MVP"
- Expanding scope (new integrations, payment methods, etc.) before MVP launch
- Any work that mixes long-term vision into the current sprint

**Default answer to "should we build X?":** "Capture it in DECISIONS.md as 'Parked', don't build it."

## Low Risk — Agent may do without asking
- Fixing typos, broken links, inconsistencies in code
- Editing/polishing existing MVP features (clarity, performance)
- Writing tests + documentation for completed work
- Updating PROJECT_STATE.md, ITERATION_LOG.md

## Medium Risk — Proceed only if clearly serves MVP launch
- Restructuring code for better maintainability
- Optimizing API responses (if not delaying launch)
- Adding logging/monitoring (if not delaying launch)

## High Risk — Ask Cody first
- Any Tier 2 feature (see scope-creep condition)
- Changing architecture decisions (D-001, D-003)
- External dependencies (new libraries, services)
- Scope changes of any kind

## Critical — Never without Cody's explicit approval
- Publishing/deploying to production
- Setting up payment processing or taking real money
- Customer communication or announcements
- Database migrations or schema changes on live data

## Current Blockers
- 🔴 **Stripe payment key approval** (external, not agent-driven)
  - Impact: Can't complete D-004; blocks MVP launch
  - Mitigation: Started integration stub; ready to wire when key arrives
  - ETA: 2026-06-10 (24-48 hours)

## After Each Work Session
Update PROJECT_STATE.md, ITERATION_LOG.md, AGENT_CONTEXT.md. Surface any decision Cody needs.
