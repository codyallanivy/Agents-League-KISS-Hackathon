#!/usr/bin/env python3
"""Asset Governor — applies KISS methodology and risk assessment to agentic
asset generation. Enforces ASSET_POLICY.md: tier scope, cost-before-spend,
content rules, and the verification-debt brake. Every request is traced.
"""

import json
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACES = HERE / "traces"

BLOCKED_TERMS = ["gore", "nude", "real person", "celebrity", "swastika", "hate symbol"]
VIDEO_TERMS = ["video", "animate", "animated", "animation", "music", "voice"]
# Tier-1 quotas per asset kind. Neutral, domain-agnostic kinds are first; the
# trailing legacy kinds keep the optional fantasy template governed correctly.
TIER1_TYPES = {"cover": 1, "logo": 1, "palette": 1, "banner": 2, "mockup": 2,
               "diagram": 1, "card": 2,
               "portrait": 4, "map": 1, "title-card": 2}
SESSION_CAP_IMAGES = 12
SESSION_CAP_USD = 2.00
VERIFICATION_CAP = 8
COST_PER_IMAGE = {"offline-svg": 0.0, "foundry-image": 0.04}


class AssetGovernor:
    def __init__(self, project_dir):
        self.project = Path(project_dir)
        TRACES.mkdir(exist_ok=True)
        self.trace_path = TRACES / time.strftime("assets-%Y%m%d.jsonl")
        self.counts = {}
        self.spend = 0.0
        self.images = 0

    # ---- the policy check (BEFORE any generation) ---------------------------
    def check(self, asset_type, prompt, mode="offline-svg"):
        cost = COST_PER_IMAGE.get(mode, 0.04)
        verdict, reasons = "ACCEPT", []

        low = prompt.lower() + " " + asset_type.lower()
        if any(t in low for t in BLOCKED_TERMS):
            verdict, reasons = "BLOCK", ["content/rights rule violation (see ASSET_POLICY.md)"]
        elif any(t in low for t in VIDEO_TERMS):
            verdict, reasons = "BLOCK", ["AI video/audio is parked (DECISIONS.md D-H03) — Tier 2"]
        elif asset_type not in TIER1_TYPES:
            verdict, reasons = "WARN", [f"'{asset_type}' is not a Tier 1 asset type — park or confirm"]
        elif self.counts.get(asset_type, 0) >= TIER1_TYPES[asset_type]:
            verdict, reasons = "WARN", [f"Tier 1 quota for '{asset_type}' reached "
                                        f"({TIER1_TYPES[asset_type]}) — further ones are Tier 2 polish"]

        if self.unreviewed_count() > VERIFICATION_CAP:
            verdict, reasons = "BLOCK", [f">{VERIFICATION_CAP} unreviewed assets — verification-debt "
                                         "brake: review existing assets before generating more"]
        if self.images + 1 > SESSION_CAP_IMAGES or self.spend + cost > SESSION_CAP_USD:
            verdict, reasons = "BLOCK", ["session budget cap reached (ASSET_POLICY.md)"]
        elif (self.spend + cost) > 0.8 * SESSION_CAP_USD and verdict == "ACCEPT":
            verdict, reasons = "WARN", ["over 80% of session budget"]

        decision = {"verdict": verdict, "reasons": reasons, "asset_type": asset_type,
                    "estimated_cost_usd": cost, "mode": mode,
                    "session_spend_usd": round(self.spend, 2), "session_images": self.images}
        self._trace(prompt, decision)
        return decision

    def record_generation(self, asset_type, path, cost):
        self.counts[asset_type] = self.counts.get(asset_type, 0) + 1
        self.images += 1
        self.spend += cost
        pv = self.project / "PENDING_VERIFICATION.md"
        if not pv.exists():
            pv.write_text("# Pending Verification — Generated Assets\n\n"
                          "> Source of truth for: assets generated but not yet human-reviewed.\n\n",
                          encoding="utf-8")
        with open(pv, "a", encoding="utf-8") as f:
            f.write(f"- [ ] {time.strftime('%Y-%m-%d')} | {asset_type} | {path} | unreviewed\n")

    def unreviewed_count(self):
        pv = self.project / "PENDING_VERIFICATION.md"
        if not pv.exists():
            return 0
        return len(re.findall(r"^- \[ \]", pv.read_text(encoding="utf-8"), re.M))

    def park(self, asset_type, prompt, reasons):
        dec = self.project / "DECISIONS.md"
        with open(dec, "a", encoding="utf-8") as f:
            f.write(f"- **D-A{int(time.time()) % 10000}** | {time.strftime('%Y-%m-%d')} | "
                    f"Parked asset request: {asset_type} — '{prompt[:80]}' | "
                    f"Why: {'; '.join(reasons)} | Revisit: after Tier 1 assets verified\n")

    def _trace(self, prompt, decision):
        with open(self.trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                "agent": "AssetGovernor", "prompt": prompt,
                                "output": decision}, ensure_ascii=False) + "\n")
