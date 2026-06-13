#!/usr/bin/env python3
"""KISS AI-Collaboration Certification — Track 2: Reasoning Agents.

Multi-agent enterprise learning system (Microsoft Foundry + the three IQ
layers) that teaches and certifies teams on the KISS methodology, with an
applied exam that performs live scope governance on a real project.

Usage:
  python main.py                 # full demo: learner journeys + scope exam + manager view
  python main.py --learner L-1001
  python main.py --request "Add blockchain payment integration"
"""

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from agents.base_agent import AgentContext, ModelClient, TraceLogger
from agents.orchestrator import KISSOrchestrator
from iq.foundry_iq import FoundryIQ
from iq.fabric_iq import FabricIQ
from iq.work_iq import WorkIQ

ROOT = Path(__file__).resolve().parent
PIZZA = ROOT.parent / "demo-project" / "pizza-shop"


def load_learners():
    raw = json.loads((ROOT / "data" / "learners.json").read_text(encoding="utf-8"))
    return raw["learners"] if isinstance(raw, dict) else raw


def build_context():
    foundry = FoundryIQ([ROOT / "knowledge", PIZZA, PIZZA / "agile"])
    fabric = FabricIQ(ROOT / "data" / "ontology.json")
    work = WorkIQ(ROOT / "data" / "work_signals.json")
    return AgentContext(foundry, fabric, work, ModelClient(), TraceLogger())


def show(title, text):
    print("\n" + "=" * 62 + "\n" + title + "\n" + "-" * 62 + "\n" + text)


def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--learner", help="run journey for one synthetic learner id")
    ap.add_argument("--request", help="run the applied scope exam for a feature request")
    args = ap.parse_args()

    ctx = build_context()
    orch = KISSOrchestrator(ctx)
    learners = load_learners()
    vision_path = PIZZA / "agile" / "PRODUCT_VISION.md"
    vision = vision_path.read_text(encoding="utf-8") if vision_path.exists() else ""

    print("KISS Certification Reasoning Engine  |  model:", ctx.model.mode)
    print("Synthetic data only — no real persons or tenant data.")
    print("Trace file:", ctx.tracer.path.name)

    if args.request:
        r = orch.scope_request(args.request, vision)
        show("APPLIED SCOPE EXAM — " + repr(args.request),
             r["answer"] + "\nCritic: " + r["critic"]["verdict"])
        return

    targets = [l for l in learners if not args.learner or l["learner_id"] == args.learner]
    for learner in targets[: (1 if args.learner else 2)]:
        j = orch.learner_journey(learner)
        lines = ["[" + name + "] " + step["answer"] for name, step in j["steps"].items()]
        show("LEARNER JOURNEY — " + learner["learner_id"] + " (" + learner["role"] + ") → "
             + j["target_certification"],
             "\n\n".join(lines) + "\n\nCritic: " + j["critic"]["verdict"])

    if not args.learner:
        r = orch.scope_request("Add blockchain payment integration", vision)
        show("APPLIED SCOPE EXAM — 'Add blockchain payment integration'",
             r["answer"] + "\nCritic: " + r["critic"]["verdict"])

        t = orch.team_insights(learners)
        show("MANAGER INSIGHTS (aggregate, synthetic IDs only)", t["answer"])

    print("\nFull reasoning trace: traces/" + ctx.tracer.path.name
          + "\nQuery it:  python query.py \"blockchain\"")


if __name__ == "__main__":
    main()
