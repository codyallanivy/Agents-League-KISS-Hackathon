# Asset Generation Policy (ASSET_POLICY.md)

> **Source of truth for:** the rules governing every AI-generated creative asset (images, and — when unparked — video) in this project. The Asset Governor enforces this file; humans amend it.

## Decision semantics

Every asset request is checked BEFORE generation: **ACCEPT** (in policy + budget → generate), **WARN** (borderline → generate only with `--confirm`, logged), **BLOCK** (out of policy → refused, parked in DECISIONS.md).

## Tier scope (per campaign project)

- **Tier 1 (build):** 1 cover art, up to 4 character portraits, 1 region map, 1 session-title card
- **Tier 2 (park):** alternate outfits/poses, per-encounter art, animated/video assets, ambient music
- **Tier 3 (park):** full illustrated rulebook, voice-acted scenes

## Budget rules (cost before spend)

- Estimated cost is computed and shown BEFORE every generation call
- Session cap: **$2.00** or **12 images**, whichever first (offline SVG mode: $0, cap still counts)
- When 80% of cap is reached: WARN on every further request

## Content & rights rules

- No real-person likenesses; no living-artist style mimicry by name
- Original content only; no franchise/trademarked IP (no trademarked characters or creatures — use generics)
- Age-appropriate (PG-13); no gore, no hate symbols
- AI video: policy applies when feature is unparked (see DECISIONS.md D-H03)

## Verification debt

Every generated asset enters `PENDING_VERIFICATION.md` (status: unreviewed). At **>8 unreviewed assets**, the governor BLOCKS new generation until a human review session clears the queue.

## Audit

Every request — verdict, cost estimate, prompt, output path — is logged to `traces/assets-*.jsonl`, queryable with the Track 2 `query.py` pattern.
