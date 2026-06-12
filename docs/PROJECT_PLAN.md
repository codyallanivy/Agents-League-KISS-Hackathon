# Agents League Hackathon: KISS Agile Studio Multi-Track Submission

> **Status:** PLAN (awaiting Cody approval before build starts)
> **Target:** Microsoft Agents League Hackathon (June 4-14, 2026)
> **Tracks:** Creative Apps (GitHub Copilot CLI) + Reasoning Agents (Copilot Studio) + Enterprise Agents (M365 Copilot)
> **Solo Builder:** Yes
> **Deadline:** June 14, 2026 11:59 PM Pacific

---

## 📋 Master Plan (FOR APPROVAL)

### Track 1: Creative Apps — GitHub Copilot CLI Integration
**Days 1-2 | Effort: 8-10 hours**

Build a custom Copilot CLI skill that embeds KISS methodology:
- `@kiss init <project-name>` → Creates PROJECT_STATE.md, DECISIONS.md, RISK_POLICY.md, TODO.md
- `@kiss status` → Reads PROJECT_STATE, recalls sprint goal (memory never resets)
- `@kiss request <feature>` → Scope checker blocks Tier 2/3 requests, parks in DECISIONS.md
- System instruction: Load AGENTS.md (Agile Coach persona) + RISK_POLICY.md (enforcement rules)

**Deliverable:** Working CLI skill + Pizza Shop demo project

---

### Track 2: Reasoning Agents — Copilot Studio + Power Automate
**Day 3 | Effort: 6-8 hours**

Create "KISS Agile Operator" agent in Copilot Studio:
- Knowledge base: Ingest all `.md` files (AGENTS.md, RISK_POLICY.md, PRODUCT_VISION.md, BRAND VOICE)
- Power Automate Flow 1: Project initialization (Teams UI → OneDrive folder → KISS files)
- Power Automate Flow 2: Scope checking (validates request → parks if out-of-scope)
- Teams integration: Daily risk report posted to channel

**Deliverable:** Copilot Studio agent + 2 Power Automate flows

---

### Track 3: Enterprise Agents — VSCode Extension + Live Dashboard
**Day 4 | Effort: 8-10 hours**

**VSCode Extension:**
- Command: "KISS: Initialize Project" (wraps CLI)
- Sidebar: TODO counter + Blocked count + Links to KISS files
- Scope warnings: Highlight Tier 2 keywords in yellow

**Live Dashboard (React):**
- Reads PROJECT_STATE.md + TODO.md from local folder
- Shows 4-column board: Now (doing) | Next (pending) | Later (parked) | Blocked
- Popsicle Index score (complexity metric: 0-100)
- Auto-updates when CLI modifies files

**Deliverable:** VSCode extension + React dashboard component

---

### Submission & Demo
**Day 5 | Effort: 5-6 hours**

- **3-minute demo video:** CLI init → scope block → dashboard update → Teams message
- **GitHub repo:** CLI skill source + extension + dashboard + architecture diagram + Pizza Shop demo
- **Judges brief:** 1-2 page narrative (Problem/Solution/Proof)
- **Submit** to hackathon portal

---

## 🎯 Why This Wins (Narrative)

### Problem
AI assistants are powerful but forgetful. Developers lose project context between sessions, scope creep derails plans, and governance is missing from enterprise tooling.

### Solution
Embed **KISS methodology** (proven durable memory system) into **Copilot CLI as default agile project manager**.

### Proof (Demo Shows)
1. Scope blocking: User requests Tier 2 feature → Agent blocks it → Auto-parks in decisions
2. Memory: Close/reopen CLI → Agent recalls sprint goal (no context loss)
3. Visibility: Dashboard shows scope health in real-time
4. Scale: Same methodology works in VSCode, Teams, and M365

### Differentiator
**"Anti-waste" philosophy:** Not anti-AI. Anti-wasting tokens/compute on out-of-scope work.

---

## 📊 Risk Assessment (Per Your RISK_POLICY)

| What | Risk Level | Why | Mitigation |
|---|---|---|---|
| All 3 tracks in 5 days, solo | Medium-High | Aggressive timeline | Cut VSCode ext if needed (Day 4 PM only) |
| Scope creep on dashboard | Medium | "Just one more feature" | Stop at MVP (4-column + index) |
| No real M365 tenant for Studio | Low | Use free trial | Pre-create trial account Day 0 |
| Demo video quality | Low | Simple screen record is fine | Judges care about concept, not production |
| Integration testing | Medium | Multiple tools need to play nice | Focus on CLI (core) → extend others |

---

## 🗓️ Day-by-Day Breakdown

### Day 1: CLI Scaffolding + File Generator
- [ ] Clone Copilot CLI repo (or review dev setup)
- [ ] Create `@kiss` skill stub
- [ ] Load AGENTS.md + RISK_POLICY.md as system instructions
- [ ] Build file generator (templates for all 5 KISS files)
- [ ] **Git checkpoint:** `day1-cli-scaffold`

### Day 2: Scope Blocker + Memory Test
- [ ] Implement Tier 2/3 detection (parse PRODUCT_VISION.md)
- [ ] Block logic: reject + park in DECISIONS.md
- [ ] Session memory: CLI reads PROJECT_STATE.md at startup
- [ ] Create Pizza Shop demo project
- [ ] Dry-run full demo end-to-end
- [ ] **Git checkpoint:** `day2-scope-enforcement`

### Day 3: Copilot Studio Agent + Power Automate
- [ ] Set up Copilot Studio environment
- [ ] Create "KISS Agile Operator" agent, ingest .md files
- [ ] Power Automate Flow 1: Project init (creates OneDrive folder + files)
- [ ] Power Automate Flow 2: Scope check (mirrors CLI logic)
- [ ] Teams integration: Daily risk report
- [ ] **Git checkpoint:** `day3-studio-agent`

### Day 4: VSCode Extension + Dashboard
- [ ] Scaffold VSCode extension
- [ ] Add "KISS: Initialize" + "KISS: Show Status" commands
- [ ] Build React dashboard component
- [ ] Wire file watching (updates on save)
- [ ] Test all integrations play together
- [ ] **Git checkpoint:** `day4-ide-dashboard`

### Day 5: Demo + Submission
- [ ] Record 3-minute demo video (all 3 tracks in action)
- [ ] Push GitHub repo (clean, public, documented)
- [ ] Write judges brief
- [ ] Fill hackathon submission form
- [ ] Submit before 11:59 PM Pacific
- [ ] **Git checkpoint:** `day5-submission`

---

## 📁 Folder Structure

```
Agents-League-KISS-Hackathon/
├── cli-skill/                    # Copilot CLI custom skill
│   ├── src/
│   ├── templates/                # KISS file templates
│   └── README.md
├── copilot-studio/               # Copilot Studio agent + flows
│   ├── agent-config.json
│   ├── power-automate-flows/
│   └── README.md
├── vscode-extension/             # VSCode extension
│   ├── src/
│   ├── package.json
│   └── README.md
├── dashboard/                    # React dashboard component
│   ├── src/
│   ├── public/
│   └── package.json
├── demo-project/                 # Pizza Shop example (created by CLI)
│   └── README.md
├── docs/                         # Architecture diagrams, brief, narrative
│   ├── ARCHITECTURE.md
│   ├── JUDGES_BRIEF.md
│   └── DEMO_SCRIPT.md
└── PROJECT_PLAN.md               # This file
```

---

## ✅ Approval Checklist

**Before build starts, Cody must approve:**

- [ ] This timeline is realistic for you (5 days, solo)
- [ ] The 3-track approach (CLI + Studio + Dashboard) is what you want
- [ ] GitHub Copilot CLI is the right hackathon target (vs other tracks)
- [ ] Pizza Shop is a good demo project (or pick different)
- [ ] You have M365 access for Copilot Studio (or can get free trial)
- [ ] You're OK with "cutting" VSCode extension if we fall behind

**Once approved, I will:**
1. Start with CLI skill (most critical path)
2. Build in parallel: Studio flows + Dashboard component
3. Daily commits to Git with progress
4. Daily summary updates to this file

---

## 🚀 Ready to Start?

**Waiting for your go-ahead on this plan. Any changes?**

- Want different demo project?
- Want to skip a track?
- Different timeline expectations?
- Questions on any phase?

Just let me know, and we build.

---

*DigitalQuill Labs × Copilot Agents League: Anti-Waste Agile for the AI Age*
