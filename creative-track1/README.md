# Track 1: Creative Apps — KISS Intake Studio (governed, domain-neutral creation)

> **The creative layer.** An adaptive survey (the KISS intake interview) turns *any* idea into a fully **governed** project: a primary creation document plus a small asset kit — where every asset request passes a policy check (ACCEPT ✅ / WARN ⚠️ / BLOCK 🚫) with a **cost estimate before any compute is spent**.
> Built with AI-assisted development (GitHub Copilot / Claude) per track guidance.

## Domain-neutral by design

The intake studio works for any project — a brand, an app, a course, an event, a product, a content plan. It does **not** optimize for any single example. There are no fantasy/RPG defaults, names, or art anywhere in the core path; the tone you give selects a clean, modern palette and the asset kit is planned from what *your* project actually needs.

## Why this is different

Most asset generators just generate. This one applies the KISS methodology and risk assessment to agentic asset generation:

- **`templates/ASSET_POLICY.md`** — the policy manual: tier scope, budget caps, content & rights rules (no real-person likenesses, no trademarked/franchise IP), verification-debt brake.
- **`asset_governor.py`** — enforces the policy *before* generation: tier quotas, cost-before-spend, blocked content, and a brake that halts generation when >8 assets sit unreviewed in `PENDING_VERIFICATION.md`.
- **Reference-grounded** — the studio searches the project's own references (intake answers, vision tiers, related approved knowledge) *before* writing the creation document or planning any asset, so output reflects the project, not a fixed template.
- **Audit trail** — every request (verdict, reasons, cost, prompt) goes to `traces/assets-*.jsonl`; blocked/parked requests are logged to the project's `DECISIONS.md` with revisit triggers.

## Run it

```bash
python intake_studio.py --preset    # demo intake → creation doc + governed assets ($0, offline SVG art)
python intake_studio.py             # interactive intake survey
```

Outputs land in `output/<project>/`: the KISS project files (PROJECT_STATE, PRODUCT_VISION with tiers, RISK_POLICY incl. your off-limits, DECISIONS), `CREATION.md` (the primary creation document — seeded and reproducible offline), and `assets/*.svg` (clean brand/product-style kit: cover, logo, palette, diagram, card…). With Microsoft Foundry configured, prose and art upgrade to model-generated (image cost estimates then become real ~$0.04/image against the same budget caps).

## Layered architecture (reads Tracks 2+3)

The studio scaffolds the same KISS file set the Track 2 reasoning engine consumes — point `foundry-track2/main.py` at any project and the Assessment Agent governs *its* scope too. Asset traces use the same JSONL schema as Track 2, queryable with the same query tool. Fabric IQ pattern: the asset tiers/quotas/rules in ASSET_POLICY.md mirror the ontology-rule approach in `data/ontology.json`; Foundry IQ pattern: creation content cites the survey-locked vision files.

## Optional: the Fantasy Campaign template (a fully isolated example)

`fantasy-template/campaign_studio.py` is an optional, self-contained example showing the system is general enough to even author a tabletop-RPG campaign. It is **deliberately isolated**: it writes only into `fantasy-template/`, it is never discovered as a project by the Command Center, and its output is never indexed into the shared knowledge base — so it cannot influence how any other project is planned or generated. Launch it on purpose via `start.bat` → option 3, or `python fantasy-template/campaign_studio.py --preset`.

## Demo art note

Offline mode renders original SVG compositions (palette driven by your tone answer; the vision board's legend encodes project state — shadows = blockers, parked lane = parked ideas, horizon = deadline). All content is original; the policy explicitly blocks franchise IP and real-person likenesses.
