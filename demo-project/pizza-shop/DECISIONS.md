# Decisions

## D-001
**Date:** 2026-06-08 09:00
**Title:** Architecture: TypeScript + React
**Why:** Type safety prevents bugs in ordering logic; React components scale to Tier 2 features (team dashboard, analytics)
**Status:** Active
**Revisit:** Never — locked in for MVP

## D-002
**Date:** 2026-06-08 14:00
**Title:** Enterprise analytics deferred to Tier 2
**Decision:** Analytics dashboard, team metrics, usage reporting = Tier 2 (post-launch)
**Why:** RISK_POLICY scope control. MVP is single-shop ordering. Analytics adds 20+ hours; blocks launch.
**Status:** Parked
**Revisit:** After first 10 sales

## D-003
**Date:** 2026-06-09 10:30
**Title:** MVP scope: Tier 1 only
**Decision:** Orders, menu, basic checkout. No: payments, accounts, delivery tracking, notifications.
**Why:** Keep launch runway short. Each added feature = 5-10 hours + test debt. Validate the core idea first.
**Status:** Active
**Revisit:** After launch feedback (week 1)

## D-004
**Date:** 2026-06-09 13:00
**Title:** Payment processing blocked — awaiting approval
**Decision:** Cannot ship without payments. Waiting for Stripe API key approval (24-48 hours).
**Why:** Customer requirement (can't take orders without payment). Blocking D-003 (full launch).
**Status:** Blocked
**Revisit:** Once Stripe approves (expected 2026-06-10)

## D-005
**Date:** 2026-06-09 14:15
**Title:** Menu structure: Simple JSON, not database
**Decision:** Store menu items in JSON file (local or CDN). No database needed for MVP.
**Why:** Keep deployment simple. No DevOps, no migrations, no infrastructure cost. Menu updates via file upload.
**Status:** Active
**Revisit:** If menu grows >1000 items or multi-location (Tier 2)
