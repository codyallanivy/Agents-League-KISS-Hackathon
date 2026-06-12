# Copilot CLI: KISS Agile Operator Design

> **Status:** ARCHITECTURE (ready for build)
> **Core insight:** Solve the real gaps in KISS methodology by embedding them in CLI
> **Timeline:** Days 1-2 of hackathon

---

## The Gap Analysis: What We're Fixing

### Old Problem → CLI Solution

| Problem (From Audit) | How CLI Solves It |
|---|---|
| **Design decisions scattered in chat** | CLI auto-logs every decision to DECISIONS.md with timestamp + why + revisit trigger |
| **Agents forget context when task-switching** | CLI loads PROJECT_STATE + DECISIONS + ITERATION_LOG at startup (full context refresh) |
| **You don't know when iteration is done** | CLI tracks checkboxes [x] and allows bulk-mark iteration "complete" with timestamp |
| **Token usage is blind spot** | CLI categorizes tasks by weight (light/medium/heavy) and displays token estimate |
| **Brand/personality gets lost** | CLI asks for user's web/social links at init, extracts tone, embeds in system instructions |
| **Multi-agent handoff is broken** | CLI auto-updates AGENT_CONTEXT.md: who worked, what they did, what's next, open questions |

---

## CLI Commands (MVP)

### Initialize Project
```bash
@kiss init <project-name>
# Prompts for:
# - Project description
# - Tier 1 scope (what's NOT in v1?)
# - Social links / web pages (to extract brand voice)
# - Team members (if multi-agent, seeds AGENT_CONTEXT.md)

# Creates:
# - PROJECT_STATE.md
# - DECISIONS.md (with template header)
# - RISK_POLICY.md (from your template, customized to scope)
# - TODO.md (with checkbox tracking + token weight column)
# - ITERATION_LOG.md (with iteration_number + completion_at tracking)
# - AGENT_CONTEXT.md (new: tracks multi-agent handoff)
# - BRAND_VOICE.md (new: personality extracted from user links)
```

### Show Project Status
```bash
@kiss status
# Displays:
# - Current sprint goal (from PROJECT_STATE)
# - Last 3 decisions with "why" (from DECISIONS)
# - TODO summary: [ ] 5 | [x] 3 | [~] 1 (from TODO.md)
# - Current iteration: active/complete
# - Token estimate for today: Light(500) + Medium(2k) + Heavy(5k) = 7.5k tokens
# - Who worked last: (from AGENT_CONTEXT)
# - Next best task recommended
```

### Request Feature / Task
```bash
@kiss request "Add email notifications"
# CLI checks:
# - Is this in PRODUCT_VISION v1 scope?
# - If no: Block + show RISK_POLICY message + park in DECISIONS.md
# - If yes: Proceed + ask what to add to TODO
# - Logs decision: "Feature: Email notifications | Why: Customer requested | Tier: 1 | Revisit: After first release"
```

### Mark Task Done
```bash
@kiss done <task-id>
# Updates TODO.md: [ ] → [x]
# Adds timestamp
# If all tasks in iteration [x]: allows @kiss complete-iteration <num>
```

### Complete Iteration
```bash
@kiss complete-iteration <num>
# Marks all tasks verified
# Appends to ITERATION_LOG.md:
#   Iteration: 3 | Status: Complete | Tasks: 5/5 done | Duration: 3h 20m | Decisions: 2 | Confidence: 95%
# Auto-generates summary entry
```

### Generate Summary
```bash
@kiss summarize
# Outputs:
# - Work completed this session
# - Decisions made (with why)
# - Blocked items + why
# - Recommended next task
# - Confidence score (0-100 based on pending verification)
# - Token usage: actual vs estimated
# 
# Appends entry to ITERATION_LOG.md
```

### View Decisions
```bash
@kiss decisions
# Shows all decisions in reverse chronological order
# Format: DATE | DECISION | WHY | STATUS (open/revisited/closed)
# Highlights: decisions pending revisit
```

### Set Brand Voice
```bash
@kiss brand-update <social-url>
# Re-parse user's web/social data
# Update BRAND_VOICE.md
# Embed updated personality into system instructions
```

---

## Core Features: How They Work

### 1. Full Context Load at Startup
```
@kiss status
↓
Reads: PROJECT_STATE.md + DECISIONS.md + RISK_POLICY.md + ITERATION_LOG.md + AGENT_CONTEXT.md
↓
Displays summary: sprint goal | recent decisions | current task | token estimate
↓
Agent system instruction now includes all this context
```

**Why:** This solves "agents forget context when switching tasks." Every session knows exactly where you are.

---

### 2. Decision Logging with "Why"
```
When user makes decision or agent recommends action:
↓
CLI auto-logs to DECISIONS.md:
  D-023 | 2026-06-09 14:30 | Feature: Email notifications | 
  Why: Tier 1 scope requirement, customer feedback in backlog | 
  Status: Active | Revisit: After v1 launch
↓
Appends timestamp, links to source (backlog item, etc.)
```

**Why:** No more "why did we decide this?" questions. Every decision has a rationale trail.

---

### 3. Checkbox Completion + Iteration Status
```
TODO.md structure:
  [ ] Design email template | light | D-023
  [x] Implement send function | medium | D-023
  [x] Write tests | medium | D-023
  [~] User testing (blocked on QA team) | light | 

Summary: 2/4 done, 1 blocked
Can run: @kiss complete-iteration 3 (only if all non-blocked items are [x])
↓
ITERATION_LOG.md records:
  Iteration: 3 | Complete | Date: 2026-06-09 | Duration: 4h | Tasks: 3/3 done | 
  Decisions: 2 | Blocked: 1 | Confidence: 90%
```

**Why:** You know when an iteration is *actually* done, not just "mostly done." Blocked items don't prevent closure.

---

### 4. Token Weight Categorization
```
TODO.md adds column:
  [ ] Design email template | light | D-023
  [x] Implement send function | heavy | D-023
  [x] Write tests | light | D-023

@kiss status shows:
  Token estimate for current sprint:
    Light (1-500 tokens): 2 tasks = 500 tokens
    Medium (500-2k tokens): 0 tasks = 0 tokens
    Heavy (2k-5k tokens): 1 task = 3k tokens
    Super-heavy (5k+ tokens): 0 tasks = 0 tokens
    ─────────────────────────────────────
    Total estimated: ~3.5k tokens

  Recommendation: "This sprint is medium complexity. Good batch size."
```

**Why:** You can see how much compute you're about to spend. "Should I add another heavy task?" becomes answerable.

---

### 5. Brand Voice from User Data
```
@kiss init pizza-shop
↓
CLI asks: "Where can I learn about your brand/voice? (social links, website, etc.)"
User provides: instagram.com/pizza-shop, pizza-shop.com
↓
CLI parses:
  - Visual style: Warm, rustic, hand-drawn
  - Tone: Conversational, slightly witty, local-focused
  - Values: Quality over speed, family-owned, community
↓
Stores in BRAND_VOICE.md:
  Style: Warm, rustic, conversational
  Examples: "We're not fancy, we're really good"
  Do: Emphasize quality, community, authenticity
  Don't: Corporate speak, mass-market positioning
↓
System instruction includes:
  "When writing copy or communications, use this brand voice: [extracted from user data]"
```

**Why:** Agents now naturally write in your voice, not generic corp-speak. Solves "coherent brand" issue.

---

### 6. Multi-Agent Handoff Protocol
```
AGENT_CONTEXT.md (auto-updated by CLI):
  ────────────────────────────────────────
  Current Agent: Cody
  Last Agent: Claude Session #42
  
  Last Agent's Work:
    - Completed: Email template design + send function
    - Status: 2 tests passing, 1 blocked on QA
    - Decisions made: D-023 (Email in Tier 1)
    - Blockers: Waiting for QA team feedback
    - Next best task: Test email edge cases
  
  Open Questions:
    - Should we support email templates from user?
    - Email rate limiting: how many per hour?
  
  Code Context:
    - Files modified: src/email.ts, tests/email.test.ts
    - Uncommitted changes: Staging area has 2 files
    - Related decisions: D-023, D-015
  ────────────────────────────────────────

When new agent starts:
  1. CLI loads AGENT_CONTEXT.md first
  2. Agent knows: what was done, what's blocked, what's next
  3. Agent asks: "Do you want me to continue where Claude left off or start fresh?"
  4. At end of session: CLI updates AGENT_CONTEXT.md with new agent's work
```

**Why:** Agents don't need to re-read entire chat history. They know the project state in 30 seconds.

---

### 7. Scope Blocker (Tier Enforcement)
```
User: "@kiss request Add enterprise SSO"
↓
CLI reads PRODUCT_VISION.md, sees:
  Tier 1 (v1, launch now): Basic auth, email, dashboard
  Tier 2 (future): SSO, analytics, team features
  Tier 3 (vision): Enterprise governance
↓
CLI response:
  "SSO is Tier 2 (future). Your Tier 1 scope is basic auth + email.
   
   I'm adding this to DECISIONS.md as a 'Parked Idea' so we don't lose it.
   
   Want to:
   a) Continue with Tier 1 work (recommended)
   b) Discuss shifting scope (risky pre-launch)
   c) Start a separate Tier 2 exploration branch?"
↓
Auto-logs to DECISIONS.md:
  D-024 | 2026-06-09 | Feature: Enterprise SSO | 
  Tier: 2 (future) | Status: Parked | Reason: RISK_POLICY scope control
```

**Why:** Prevents scope creep at the moment it happens, not after 20 hours of work.

---

### 8. Summarizer
```
@kiss summarize
↓
CLI reads ITERATION_LOG.md, recent TODO changes, DECISIONS.md
↓
Generates:
  ═══════════════════════════════════════
  Session Summary
  ═══════════════════════════════════════
  
  ✓ Work Completed
    - Email template design (light, D-023)
    - Send function implementation (heavy, D-023)
    - Basic tests (light, D-023)
    Total: 3 tasks, ~3.5k tokens estimated
  
  ◐ Blocked
    - User testing: Waiting for QA team (1 task)
    - Design review: Pending design feedback (1 task)
  
  ✎ Decisions Made
    - D-024: Enterprise SSO → Parked (Tier 2)
    - D-025: Email rate limit = 10/hour (Tier 1, customer requirement)
  
  ⚠ Open Questions
    - Should we support custom email templates?
    - Rate limiting: is 10/hour right?
  
  → Next Best Task
    Run: @kiss request "Email edge case testing"
    Effort: light (~500 tokens)
    Blocker: None
    Why: Unblocks D-025 validation
  
  Confidence: 85%
    Why: 2 blocked items, 1 open decision, tests need review
    To improve: Get QA feedback + design review
  
  ═══════════════════════════════════════
  
↓
Appends summary to ITERATION_LOG.md with timestamp
↓
Displays in console
```

**Why:** You get a clear picture of what happened, what's stuck, and what to do next. No rereading chat logs.

---

## File Schema (How Files Change)

### PROJECT_STATE.md
```markdown
# Project State

Last updated: 2026-06-09 14:35 UTC

## Current Sprint
Goal: Email notification system (Tier 1, v1 launch)
Status: In progress (2/4 tasks done, 1 blocked)
Iteration: 3 (of 4 planned for v1)

## Latest Decisions
- D-025: Email rate limit = 10/hour (active)
- D-024: Enterprise SSO = Parked (Tier 2)
- D-023: Email in Tier 1 (active)

## Work Status
Done: 2 tasks (~3.5k tokens)
In Progress: 0
Blocked: 1
Parked: 0

## Blockers
- QA team feedback pending (1 task)

## Last Agent
Cody | Session start: 2026-06-09 10:00
```

### DECISIONS.md
```markdown
# Decisions

## D-025 (Active)
Date: 2026-06-09 14:25
Title: Email rate limiting
Decision: 10 emails per hour per user (soft limit, configurable)
Why: Prevent abuse, align with customer feedback on issue #42
Status: Active
Revisit: After first week of production use
Related: D-023

## D-024 (Parked)
Date: 2026-06-09 14:20
Title: Enterprise SSO integration
Decision: Deferred to Tier 2 / post-launch
Why: Out of v1 scope per RISK_POLICY, customer not requesting
Status: Parked (not building now)
Revisit: If customer budget allows Tier 2 upgrade
```

### TODO.md
```markdown
# To Do

## Iteration 3 (Email Notifications)

- [x] Design email template | light (500) | D-023 | Done 2026-06-09 14:00
- [x] Implement send function | heavy (3k) | D-023 | Done 2026-06-09 13:45
- [ ] Email edge case testing | light (500) | D-025 | Blocked by QA
- [~] User acceptance testing | medium (1.5k) | D-023 | Blocked (awaiting QA feedback)

Status: 2/4 done, 1 blocked, 1 not started
Complete when: All non-blocked items [x]
```

### AGENT_CONTEXT.md (New)
```markdown
# Agent Context

Updated: 2026-06-09 14:35

## Current Agent
Name: Cody
Active since: 2026-06-09 10:00

## Last Agent's Work
Name: Claude (Session #42)
Duration: 45 minutes
Work completed:
  - Designed email template
  - Implemented send function
  - Started tests (2 passing, 1 failing)
Status: Stopped due to QA blocker
Decisions made: D-023
Recommended next: Email edge case testing

## Open Questions
- Should email templates support custom branding?
- Email rate limiting: is 10/hour right for your users?
- Should we cache template renders?

## Files Modified
- src/email.ts
- tests/email.test.ts
- docs/EMAIL_DESIGN.md
```

### BRAND_VOICE.md (New)
```markdown
# Brand Voice

Extracted from: instagram.com/pizza-shop, pizza-shop.com
Updated: 2026-06-09 09:30

## Personality
Warm, rustic, conversational, family-focused
Community-oriented, quality-first, anti-corporate

## Tone Examples
✓ "We're not fancy, we're really good."
✓ "Fresh ingredients from local farms. Every pizza tells a story."
✗ "Enterprise-grade pizza delivery solutions"
✗ "Disrupting the QSR space with AI-powered..."

## Key Values
1. Quality over speed
2. Community connection
3. Authenticity (not mass-market)
4. Family-owned sustainability

## Writing Guidelines
When writing copy/communications:
- Start with the human benefit, not the feature
- Use first-person or community voice ("we," "our," "you")
- Avoid jargon and corporate terms
- Lead with story/emotion, then practicality
```

---

## Success Criteria (What Makes CLI "Win")

✅ **CLI launches a project with all 7 files** (PROJECT_STATE, DECISIONS, RISK_POLICY, TODO, ITERATION_LOG, AGENT_CONTEXT, BRAND_VOICE)

✅ **Scope blocker works**: User requests Tier 2 → blocked + parked in 3 seconds

✅ **Memory never resets**: Close/reopen CLI → agent recalls full project state

✅ **Decisions are traceable**: Every decision has timestamp + why + revisit trigger

✅ **Iteration completion is crisp**: Mark iteration "done" with 1 command, timestamp recorded

✅ **Token weight visible**: See estimated tokens for current sprint before you start

✅ **Brand voice auto-embeds**: User's web/social data informs agent voice

✅ **Multi-agent handoff works**: New agent reads AGENT_CONTEXT + PROJECT_STATE, knows what to do

✅ **Summarizer generates insight**: Session summary with confidence score + next best task

✅ **Pizza Shop demo works**: Every feature tested on realistic demo project

---

## Implementation Phases (Days 1-2)

### Day 1 AM (4-5 hours)
- [ ] Create file template system (all 7 files)
- [ ] Implement `@kiss init` command (create project + prompt for brand data)
- [ ] Implement `@kiss status` command (load + display context)
- [ ] Test with Pizza Shop project

### Day 1 PM (3-4 hours)
- [ ] Implement `@kiss done` + `@kiss complete-iteration` (checkbox + iteration tracking)
- [ ] Implement `@kiss summarize` (generate session summary)
- [ ] Test iteration completion flow

### Day 2 AM (4-5 hours)
- [ ] Implement `@kiss request` + scope blocker logic
- [ ] Implement `@kiss decisions` (view decision log)
- [ ] Test scope blocking with Pizza Shop demo

### Day 2 PM (2-3 hours)
- [ ] Polish commands, error handling
- [ ] Record CLI demo video
- [ ] Prepare GitHub commit with full CLI source
- [ ] **Git checkpoint:** `day2-cli-complete`

---

## Tech Stack (TBD - Your Choice)
- Language: Node.js / Python / Go? (Fast CLI tool)
- Copilot integration: CLI SDK / custom webhook?
- File system: Local folder reading/writing
- Templating: Simple string replacement (keep it light)
- Brand extraction: Basic HTML parsing or regex (just headlines, tone words, links)

---

## Questions for Cody

1. **Language preference**: Node.js (fastest), Python (familiar), or Go (compiled)?
2. **CLI framework**: Use existing Copilot CLI SDK or build custom integration?
3. **Brand extraction**: Simple (pull headlines + tone words) or deeper (NLP-based)?
4. **Token weight formula**: Use my estimates (light=500, medium=2k, heavy=5k) or adjust?

Ready to build when you confirm.
