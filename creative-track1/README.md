# Track 1: Creative Apps — KISS Campaign Studio (governed asset generation)

> **The creative layer.** A short survey (the KISS intake interview) becomes a fully **governed** creative project: an original fantasy campaign plus art assets — where every asset request passes a policy check (ACCEPT ✅ / WARN ⚠️ / BLOCK 🚫) with a **cost estimate before any compute is spent**.
> Built with AI-assisted development (GitHub Copilot / Claude) per track guidance.

## Why this is different

Most asset generators just generate. This one applies the KISS methodology and risk assessment to agentic asset generation:

- **`templates/ASSET_POLICY.md`** — the policy manual: tier scope (Tier 1 = cover, 4 portraits, map, title-card; video/music = parked), budget caps, content & rights rules (no real-person likenesses, no franchise IP), verification-debt brake.
- **`asset_governor.py`** — enforces the policy *before* generation: tier quotas, cost-before-spend, blocked content, and a brake that halts generation when >8 assets sit unreviewed in `PENDING_VERIFICATION.md`.
- **Audit trail** — every request (verdict, reasons, cost, prompt) goes to `traces/assets-*.jsonl`; blocked/parked requests are logged to the campaign's `DECISIONS.md` with revisit triggers.

## Run it

```bash
python campaign_studio.py --preset    # demo survey → campaign + governed assets ($0, offline SVG art)
python campaign_studio.py             # interactive survey
```

Outputs land in `output/<campaign>/`: KISS project files (PROJECT_STATE, PRODUCT_VISION with tiers, RISK_POLICY incl. your off-limits table rule, DECISIONS), `CAMPAIGN.md` (three acts, NPCs, hooks — seeded and reproducible), and `assets/*.svg`. With Microsoft Foundry configured, prose and art upgrade to model-generated (image cost estimates then become real ~$0.04/image against the same budget caps).

## Layered architecture (reads Tracks 2+3)

The studio scaffolds the same KISS file set the Track 2 reasoning engine consumes — point `foundry-track2/main.py` at a campaign project and the Assessment Agent governs *its* scope too. Asset traces use the same JSONL schema as Track 2, queryable with the same query tool. Fabric IQ pattern: the asset tiers/quotas/rules in ASSET_POLICY.md are the same ontology-rule approach as `data/ontology.json`; Foundry IQ pattern: campaign content cites the survey-locked vision files.

## D&D is one use case, not the product

The studio is a general pattern: **any idea → KISS intake survey → governed project → generated understanding** (campaign, content plan, brand kit, lesson series). Modes adapt the survey — *project mode* for builders, *experience mode* for entertainment (this demo). A zero-AI **visual state engine** drives the look: your tone answer selects the palette for every asset, so the whole campaign feels art-directed for free.

## Demo art note

Offline mode renders original SVG compositions (palette driven by your tone answer; the map legend encodes project state symbolically — shadowed regions = blockers, horizon = deadline). All content is original fantasy material; the policy explicitly blocks franchise IP and real-person likenesses.
