# Track 2: Reasoning Agents — KISS AI-Collaboration Certification

> **Challenge:** Build a multi-agent enterprise learning system with Microsoft Foundry that manages internal team certification programmes.
> **Our scenario:** Fictional "Pizza Shop Co." certifies employees on the **KISS methodology** — how to collaborate with AI agents without scope creep, lost context, or wasted tokens. The applied exam is *live scope governance* on a real (synthetic) project.
> **Synthetic data only.** All learners, work signals, and documents are fabricated for demonstration. No real persons, tenant data, or PII.

## The Five Agents (challenge baseline flow)

| Agent | Role | Grounding |
|---|---|---|
| Learning Path Curator | Maps role + goal → certification + cited content | Foundry IQ + Fabric IQ role map |
| Study Plan Generator | Capacity-aware schedule, milestones | Fabric IQ (hours/thresholds) + Work IQ (focus capacity) |
| Engagement Agent | Reminders adapted to work rhythm | Work IQ signals |
| Assessment Agent | Readiness + cited practice questions + **applied scope exam** (ACCEPT/WARN/BLOCK) | Foundry IQ + Fabric IQ rules |
| Manager Insights | Aggregate readiness + capacity risk (no personal data) | Fabric IQ + Work IQ |

**Orchestrator:** planner–executor with a **critic/verifier** pass — every answer must carry citations or the critic fails the run.

## Microsoft IQ Integration (all three layers)

- **Foundry IQ** (`iq/foundry_iq.py`) — knowledge base over approved sources (`knowledge/` + the pizza-shop project files); every retrieval returns citations. Hosted version: Foundry IQ knowledge base over Blob Storage + Azure AI Search.
- **Fabric IQ** (`iq/fabric_iq.py` + `data/ontology.json`) — ontology unifying certifications, roles, skills, scope tiers, and business rules (R-1…R-5) that agents reason with.
- **Work IQ** (`iq/work_iq.py` + `data/work_signals.json`) — synthetic work-pattern signals (meeting load, focus hours) drive scheduling and engagement.

## Observability: every thought is queryable

Every agent step (prompt, grounding citations, output, model) is logged to `traces/run-*.jsonl`.

```bash
python query.py "blockchain"              # full-text search all reasoning
python query.py --agent AssessmentAgent   # one agent's steps
python query.py --prompts "tier"          # search inside prompts
python query.py --decisions "parked"      # search the decision log
```

## Run it

```bash
pip install -r requirements.txt
python main.py                                        # full demo (offline mode works out of the box)
python main.py --request "Add blockchain payment integration"   # applied scope exam → BLOCK + parked
python main.py --learner L-1001                       # one learner journey
```

**With Microsoft Foundry:** copy `.env.example` → `.env`, set `AZURE_AI_PROJECT_ENDPOINT` (+ `az login`); agents then reason through your gpt-4o deployment. Azure is an enhancement layer, not a dependency — the offline deterministic engine produces the same flow for reliable demos.

## Reasoning patterns used

Planner–Executor (orchestrator), Critic/Verifier (citation hygiene gate), role-based specialisation (five single-responsibility agents), grounded retrieval with mandatory citations (no unsupported free text).

## Outputs consumed downstream

- Track 3 (M365 governance UI) renders `traces/*.jsonl` + decision entries as Adaptive Cards for managers.
- Track 1 (creative layer) generates certification study guides and campaign assets from the same grounded knowledge.
