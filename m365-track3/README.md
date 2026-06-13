# Track 3: Enterprise Agents — KISS Governance Agent for M365 Copilot

> **The governance layer.** Reads the Track 2 reasoning engine's outputs (decision logs, reasoning traces, readiness reports) and surfaces them to managers inside Microsoft 365 Copilot as Adaptive Cards: scope decisions with WHY + audit trail, team certification readiness, and verification-debt alerts.
> **Synthetic data only** — fictional company, fabricated learner IDs.

## What's here

- `appPackage/` — production-ready **declarative agent** for M365 Copilot: `manifest.json` (Teams app manifest v1.19 with `copilotAgents`) + `declarativeAgent.json` (instructions, conversation starters, SharePoint knowledge grounding). Sideload with Teams Toolkit / Agents Toolkit on a tenant with custom app upload enabled.
- `adaptive-cards/` — three Adaptive Card templates (v1.5, data-bound): scope decision (ACCEPT/WARN/BLOCK + trace audit), team readiness, verification-debt brake.
- `mock-ui/` — because our demo tenant blocks sideloading, `build_mock.py` renders the cards into a static Teams/Copilot UI simulation **from the real Track 2 trace files** — run Track 2, rebuild, and the mock shows the actual reasoning outputs. Open `teams-mock.html` in a browser.

```bash
cd ../foundry-track2 && python main.py --request "Add blockchain payment integration"
cd ../m365-track3/mock-ui && python build_mock.py && start teams-mock.html
```

## Microsoft IQ integration

The agent's knowledge is the output of the Track 2 engine, which is grounded by all three IQ layers (Foundry IQ citations, Fabric IQ ontology rules, Work IQ capacity signals). In a live tenant, **Work IQ** additionally personalises the agent through M365 Copilot's native context, and the SharePoint capability gives permission-aware grounding over the published `kiss-outputs` library (Foundry IQ pattern).

## Governance rules embedded in the agent

Aggregate data only (no personal detail); every surfaced decision includes WHY + revisit trigger; ACCEPT/WARN/BLOCK semantics; trace run-ids cited for auditability; verification-debt brake recommendation at >2 unverified iterations.
