# Builder Studio — an IQ-governed visual builder (KISS Studio, submission #2)

> Most visual builders help you assemble screens. **Builder Studio asks whether you *should*** — every plan, component, and feature idea can be validated against your project's own vision and answered with **cited** guidance, because the canvas is plugged into the KISS reasoning engine.
> Synthetic data only; shares its intelligence backend with [KISS Studio](../README.md) — one engine, two surfaces.

## Run it

```
start.bat → option 1        (starts the engine)
open http://localhost:8765/builder-iq
```

Also runs standalone (double-click `index.html`) — the IQ dock then reports the engine offline and the canvas still works.

## Microsoft IQ integration

| Builder feature | IQ layer | How |
|---|---|---|
| **Plan with KISS** button | **Foundry IQ** | one click retrieves cited, grounded planning guidance from the project's knowledge base — answers carry source citations, the engine's critic rejects uncited output |
| **🛡 Validate scope** (IQ dock) | **Fabric IQ** | the feature you describe is classified against the active project's vision tiers using ontology rules (R-4: Tier 2/3 → parked, never built) → ACCEPT ✅ / WARN ⚠️ / BLOCK 🚫 with the why |
| **📚 Cited guidance** (IQ dock) | **Foundry IQ + project context** | file-grounded chat that reads the active project's live PROJECT_STATE / VISION / creation doc — context-aware guidance in the Work IQ pattern |
| Model status pill | model ladder | shows which brain answers: Azure Foundry (gpt-4o) → local Ollama → offline |

Every dock interaction is logged to the engine's JSONL reasoning traces — auditable in the Command Center's Data Explorer or `query.py`.

## The story

Plan → Build → Code → Test → Export. The canvas, component inspector, templates, and smart terminal are the build surface; the KISS engine underneath is the conscience: durable project memory in Markdown, scope governance grounded in *your* vision, and citations on every claim. Built solo with AI-assisted development, governed by its own methodology (decision log: `../GAP_ANALYSIS.md`).

## 90-second demo beats

1. Open `/builder-iq` — IQ pill reads the live model tier and active project
2. Click **Plan with KISS** → cited guidance appears in the dock
3. Type "add user accounts and payments" → **🛡 Validate scope** → WARN/BLOCK with the rule and the why
4. Build the Tier-1 components on the canvas → Export
5. Switch to the Command Center → the same interactions are in the reasoning traces
