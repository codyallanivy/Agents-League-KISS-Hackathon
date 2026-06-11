#!/usr/bin/env python3
"""Query prompts, logs, and reasoning traces (observability layer).

Search everything the agents thought, said, and cited — plus the project's
decision log — from one place.

Usage:
  python query.py "blockchain"                 # full-text search everywhere
  python query.py --agent AssessmentAgent      # all steps by one agent
  python query.py --prompts "tier"             # search inside prompts only
  python query.py --decisions "parked"         # search DECISIONS.md entries
  python query.py --last 5                     # last N trace steps
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACES = ROOT / "traces"
DECISION_FILES = [
    ROOT.parent / "demo-project" / "pizza-shop" / "DECISIONS.md",
    ROOT.parent / "GAP_ANALYSIS.md",
]


def iter_trace_steps():
    for f in sorted(TRACES.glob("run-*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def fmt(step, show_prompt=False):
    out = step.get("output", {})
    answer = out.get("answer") or json.dumps(out)[:200]
    s = (f"[{step.get('ts')}] {step.get('agent')} ({step.get('model', '-')}) "
         f"run={step.get('run_id')}\n  → {answer[:300]}")
    cites = step.get("grounding") or out.get("citations")
    if cites:
        s += f"\n  cites: {'; '.join(cites[:4])}"
    if show_prompt and step.get("prompt"):
        s += f"\n  prompt: {step['prompt'].get('user', '')[:300]}"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default=None)
    ap.add_argument("--agent")
    ap.add_argument("--prompts", help="search inside prompts only")
    ap.add_argument("--decisions", help="search decision log entries")
    ap.add_argument("--last", type=int)
    args = ap.parse_args()

    if args.decisions is not None:
        q = args.decisions.lower()
        for f in DECISION_FILES:
            if not f.exists():
                continue
            hits = [l for l in f.read_text(encoding="utf-8").splitlines()
                    if l.strip().startswith(("- **D-", "## D-", "| D-")) and q in l.lower()]
            for h in hits:
                print(f"{f.name}: {h.strip()}")
        return

    steps = list(iter_trace_steps())
    if args.agent:
        steps = [s for s in steps if s.get("agent") == args.agent]
    if args.prompts:
        q = args.prompts.lower()
        steps = [s for s in steps if q in json.dumps(s.get("prompt", {})).lower()]
    elif args.text:
        q = args.text.lower()
        steps = [s for s in steps if q in json.dumps(s).lower()]
    if args.last:
        steps = steps[-args.last:]

    if not steps:
        print("No matching trace steps. Run `python main.py` first.")
        return
    for s in steps:
        print(fmt(s, show_prompt=bool(args.prompts)) + "\n")
    print(f"({len(steps)} step(s) matched)")


if __name__ == "__main__":
    main()
