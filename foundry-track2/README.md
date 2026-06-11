# Track 2: Reasoning Agents - KISS Multi-Agent Orchestration

**Challenge:** Build a multi-agent enterprise learning system using Microsoft Foundry.

**KISS Adaptation:** Replace "learning" with "project scope enforcement." Agents reason about scope, decisions, and task planning using .md files as grounded knowledge.

## Agents

1. **Scope Evaluator** — Reads PRODUCT_VISION.md, checks if feature is Tier 1/2/3
2. **Decision Reasoner** — Reads DECISIONS.md, understands past WHY reasoning
3. **Planner Agent** — Reads TODO.md + PROJECT_STATE.md, estimates effort + blockers
4. **Recommender Agent** — Synthesizes all above, recommends action
5. **Manager Insights Agent** — Reports popsicle index + scope health

## Architecture

```
User Request
  ↓
Foundry Orchestrator
  ├─ Scope Evaluator (reads PRODUCT_VISION.md)
  ├─ Decision Reasoner (reads DECISIONS.md)
  ├─ Planner Agent (reads TODO.md)
  └─ Recommender (synthesizes)
  ↓
Response with reasoning trace
  ↓
Update PROJECT_STATE.md / DECISIONS.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure Azure
cp .env.example .env
# Fill in AZURE_AI_PROJECT_ENDPOINT, etc.

# Run
python main.py
```

## Next Steps

- [ ] Install Azure AI SDK
- [ ] Create agent definitions
- [ ] Wire Foundry IQ knowledge base
- [ ] Implement reasoning loop
- [ ] Test with pizza shop scenario
