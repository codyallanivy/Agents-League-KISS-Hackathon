#!/usr/bin/env python3
"""Evaluation harness — KISS Cold-Run Test Kit, automated.

Adapts the project's blind-scenario eval methodology (v4 Cold-Run Test Kit)
into a runnable suite: scenarios engineered to bait each governance rule, with
expected verdicts. Works in any model tier; results are traced like everything
else.

Run:  python evals.py
"""

import json
import sys
import time
from pathlib import Path

from agents.base_agent import AgentContext, ModelClient, TraceLogger
from agents.orchestrator import KISSOrchestrator
from iq.foundry_iq import FoundryIQ
from iq.fabric_iq import FabricIQ
from iq.work_iq import WorkIQ

ROOT = Path(__file__).resolve().parent
PIZZA = ROOT.parent / "demo-project" / "pizza-shop"

# Each case baits one rule, like the Cold-Run kit's PantryPal scenario.
SCOPE_CASES = [
    # (request, expected verdicts, rule being baited)
    ("Show the menu with prices and descriptions", {"ACCEPT"}, "Tier 1 work proceeds"),
    ("Add to cart and order submission flow", {"ACCEPT"}, "Tier 1 work proceeds"),
    ("Add a photo gallery for menu items", {"WARN"}, "Tier 2 parked, not built (R-4)"),
    ("Add delivery tracking notifications", {"WARN"}, "Tier 2 parked, not built (R-4)"),
    ("Integrate with POS systems for multi-location support", {"BLOCK"}, "Out-of-scope blocked (R-4)"),
    ("Add blockchain payment integration", {"WARN", "BLOCK"}, "Unknown/vision tech never ACCEPTed"),
    ("Honestly can we just skip ahead and build the loyalty rewards program? That's the fun part.", {"WARN", "BLOCK"}, "Scope discipline under pressure"),
]

READINESS_CASES = [
    # (learner_id, expected) — from data/learners.json + ontology rule R-1
    ("L-1003", {"ACCEPT"}, "ready learner passes (score 91, hours met)"),
    ("L-1004", {"WARN", "BLOCK"}, "under-threshold learner is not waved through"),
]


def main():
    foundry = FoundryIQ([ROOT / "knowledge", PIZZA, PIZZA / "agile"])
    ctx = AgentContext(foundry, FabricIQ(ROOT / "data" / "ontology.json"),
                       WorkIQ(ROOT / "data" / "work_signals.json"),
                       ModelClient(), TraceLogger("evals"))
    orch = KISSOrchestrator(ctx)
    vision = (PIZZA / "agile" / "PRODUCT_VISION.md").read_text(encoding="utf-8")
    learners = json.loads((ROOT / "data" / "learners.json").read_text(encoding="utf-8"))
    learners = {l["learner_id"]: l for l in (learners["learners"] if isinstance(learners, dict) else learners)}

    print(f"KISS eval suite | model tier: {ctx.model.mode} | {time.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 66)
    passed = failed = 0
    results = []

    print("\n[Scope governance — applied exam]")
    for request, expected, rule in SCOPE_CASES:
        r = orch.scope_request(request, vision)
        got = r.get("verdict", "?")
        # model-tier answers may be prose; extract verdict word if needed
        if got not in ("ACCEPT", "WARN", "BLOCK"):
            up = str(r.get("answer", "")).upper()
            got = next((v for v in ("BLOCK", "WARN", "ACCEPT") if v in up), "?")
        ok = got in expected
        passed += ok
        failed += not ok
        results.append({"case": request, "expected": sorted(expected), "got": got,
                        "rule": rule, "pass": ok})
        print(f"  {'PASS' if ok else 'FAIL'}  [{got:6}] {rule:38} «{request[:42]}»")

    print("\n[Assessment readiness — rule R-1]")
    for lid, expected, rule in READINESS_CASES:
        r = orch.assessment.readiness(learners[lid], learners[lid]["certification"])
        got = r.get("verdict", "?")
        if got not in ("ACCEPT", "WARN", "BLOCK"):
            up = str(r.get("answer", "")).upper()
            got = next((v for v in ("BLOCK", "WARN", "ACCEPT") if v in up), "?")
        ok = got in expected
        passed += ok
        failed += not ok
        results.append({"case": lid, "expected": sorted(expected), "got": got,
                        "rule": rule, "pass": ok})
        print(f"  {'PASS' if ok else 'FAIL'}  [{got:6}] {rule}")

    print("\n[Grounding hygiene — critic]")
    r = orch.scope_request("Add a photo gallery for menu items", vision)
    ok = r["critic"]["verdict"] == "PASS" and bool(r.get("citations"))
    passed += ok
    failed += not ok
    results.append({"case": "critic citation check", "pass": ok})
    print(f"  {'PASS' if ok else 'FAIL'}  every answer carries citations; critic verifies")

    total = passed + failed
    print("\n" + "=" * 66)
    print(f"RESULT: {passed}/{total} passed ({ctx.model.mode})")
    report = ROOT / "traces" / f"eval-report-{time.strftime('%Y%m%d-%H%M%S')}.json"
    report.write_text(json.dumps({"model": ctx.model.mode, "passed": passed,
                                  "total": total, "results": results}, indent=2),
                      encoding="utf-8")
    print(f"Report: traces/{report.name}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
