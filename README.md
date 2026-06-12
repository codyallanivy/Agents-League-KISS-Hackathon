# KISS Studio — Anti-Waste Agile for the AI Age

> **Agents League Hackathon 2026 · all three tracks · all three Microsoft IQ layers**
> AI assistants are powerful but forgetful. Teams lose project context between sessions, scope creep derails sprints, and tokens burn on work nobody asked for. **KISS Studio** turns plain Markdown files into durable agent memory, enforces scope with ACCEPT ✅ / WARN ⚠️ / BLOCK 🚫 governance, and makes every AI decision **cited, traced, and queryable**.

**⚠️ Synthetic data only.** Every learner, work signal, company, and document in this repository is fabricated for demonstration. No real persons, tenant data, or PII.

## Try it in 30 seconds

```
git clone <this repo>
cd Agents-League-KISS-Hackathon
start.bat            ← option 1 opens the Command Center (needs only Python)
```

Works fully **offline** out of the box. With [Ollama](https://ollama.com) installed it upgrades to local open-weight reasoning; with an Azure Foundry endpoint in `foundry-track2/.env` it upgrades to cloud — same engine, three brains, switchable live from the dashboard (**⚖ Compare** runs one prompt through all tiers side by side).

## The three tracks (one layered system)

| Track | What it is | Where |
|---|---|---|
| 🧠 **Reasoning Agents** (foundation) | Five-agent enterprise learning system: Learning Path Curator, Study Plan Generator, Engagement, Assessment (with a live **applied scope exam**), Manager Insights — planner-executor orchestration with a **critic that fails any uncited answer** | `foundry-track2/` |
| 💼 **Enterprise Agents** (governance) | M365 Copilot **declarative agent** + Adaptive Cards rendering the engine's real decisions, readiness, and verification-debt alerts for managers | `m365-track3/` |
| 🎨 **Creative Apps** (creative layer) | **KISS Campaign Studio**: adaptive intake survey → governed project → creation document + art assets, every one passing the **Asset Governor** (policy, cost-before-spend, verification queue) | `creative-track1/` + `command-center/` |

The scenario: fictional **"Pizza Shop Co."** runs an internal **KISS AI-Collaboration Certification** — employees learn to work with AI agents without scope creep or wasted tokens, and the *practical exam* is real scope governance on live (synthetic) projects.

## Microsoft IQ integration — all three layers

| Layer | Our implementation | File |
|---|---|---|
| **Foundry IQ** | Knowledge base over approved sources; every retrieval returns **citations**; the critic fails uncited answers | `foundry-track2/iq/foundry_iq.py` |
| **Fabric IQ** | Ontology of certifications, roles, skills, scope tiers + business rules R-1…R-5 that agents **reason with** (prerequisite graphs, pass thresholds, park-don't-build) | `foundry-track2/data/ontology.json` + `iq/fabric_iq.py` |
| **Work IQ** | Synthetic work-pattern signals (meeting load, focus hours) drive scheduling, engagement, and capacity-risk flags — per the challenge's synthetic-data requirement | `foundry-track2/iq/work_iq.py` |

Each layer is a swappable local module matching the product's contract; the model tier connects to a real **Azure Foundry gpt-4o deployment** (`setup-azure.ps1` provisions it in one command).

## Evaluations & observability (run them yourself)

```
cd foundry-track2
python evals.py        # 10-case suite from our Cold-Run Test Kit — 10/10 offline
python main.py --request "Add blockchain payment integration"   # → BLOCK + parked
python query.py "prerequisite" --source ontology                # Data Explorer CLI
```

Every agent step — prompt, grounding citations, output, model tier — is appended to `traces/*.jsonl` and queryable across **six sources** (traces, decisions, knowledge, ontology, work signals, learners) from the CLI or the dashboard's Data Explorer. Compare-mode feedback is captured as chosen/rejected preference pairs — a fine-tuning-ready dataset.

## The Command Center

Three views over the same engine: **Assistant** (chat + model compare), **Project Ops** (board, scope gate, Context ROI Coach, evidence-seeded Popsicle Index, health radar, memo inbox, .ics calendar export), **Creative Studio** (creative chat that creates *and* edits projects by talking, vision board, governed asset gallery). Onboard any folder on your machine into KISS with two clicks — existing files are never modified.

## Companion submission: Builder Studio

`command-center/builder-studio-prototype.html` — the latest recovered visual builder prototype: Plan → Build → Code → Test → Export, CodeMirror code editing, selected-component styling, behavior editing, smart terminal, preview-only inspector, and local/Foundry mock controls. Run `start.bat` option 6 or open `http://localhost:8765/builder`.

`builder-studio/` is preserved as the older IQ-connected demo at `http://localhost:8765/builder-iq` for cited planning guidance, scope validation, and project-context chat.

## Why this is different

Token trackers measure what you *already spent*. KISS estimates context cost **before you spend it**, ties it to project structure, and refuses out-of-scope work by default ("capture it, don't build it"). The methodology is agent-agnostic Markdown; the integrations are Microsoft-native. Built solo with AI-assisted development (GitHub Copilot + Claude), governed by its own methodology — this repo's `GAP_ANALYSIS.md` decision log is the system eating its own popsicle.

## Repo map

`foundry-track2/` engine + IQ layers + evals · `command-center/` dashboard · `creative-track1/` campaign studio + asset governor + vision layer · `m365-track3/` declarative agent + cards + Teams mock · `demo-project/` seeded synthetic projects · `cli-skill/` Track 1 CLI origin · `docs/` demo script, judges brief, planning history · `GAP_ANALYSIS.md` living decision log
