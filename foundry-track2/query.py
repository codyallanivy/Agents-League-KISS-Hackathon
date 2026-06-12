#!/usr/bin/env python3
"""KISS Data Explorer — one query across every intelligence source.

Plug-and-play source registry: each source is an adapter with the same shape
(name, search(q) -> rows). Adding a new source (Azure AI Search, Graph, ...)
is one function. Sources:

  traces     reasoning steps: prompts, outputs, models, citations (JSONL)
  decisions  decision log entries (D-XXX) from project + repo docs
  knowledge  Foundry IQ chunks — the cited grounding itself
  ontology   Fabric IQ entities, relationships, and rules R-1..R-5
  work       Work IQ synthetic signals (meetings, focus, slots)
  learners   synthetic learner records

Usage:
  python query.py "blockchain"                 # all sources
  python query.py "meeting" --source work
  python query.py "prerequisite" --source ontology
  python query.py --agent AssessmentAgent --last 5
  python query.py --decisions "parked"         # legacy flag, still works
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACES = ROOT / "traces"
DECISION_FILES = [ROOT.parent / "demo-project" / "pizza-shop" / "DECISIONS.md",
                  ROOT.parent / "GAP_ANALYSIS.md"]


def _hit(q, *fields):
    q = q.lower()
    return not q or any(q in str(f).lower() for f in fields)


# ---- source adapters (name -> search(q) -> [row dicts]) ----------------------
def src_traces(q="", agent=None):
    rows = []
    for f in sorted(TRACES.glob("run-*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                s = json.loads(line)
            except json.JSONDecodeError:
                continue
            if agent and s.get("agent") != agent:
                continue
            if _hit(q, json.dumps(s)):
                out = s.get("output", {})
                rows.append({"src": "traces", "ts": s.get("ts"), "agent": s.get("agent"),
                             "model": s.get("model", "-"),
                             "text": (out.get("answer") or json.dumps(out)[:160])[:240],
                             "cites": (s.get("grounding") or [])[:3],
                             "run": s.get("run_id")})
    return rows


def src_decisions(q=""):
    rows = []
    for f in DECISION_FILES:
        if not f.exists():
            continue
        for l in f.read_text(encoding="utf-8").splitlines():
            if re.match(r"\s*[-|#]*\s*\**D-", l) and _hit(q, l):
                rows.append({"src": "decisions", "file": f.name, "text": l.strip()[:280]})
    return rows


def src_knowledge(q=""):
    """Foundry IQ chunks: query the cited grounding directly."""
    from iq.foundry_iq import FoundryIQ
    pizza = ROOT.parent / "demo-project" / "pizza-shop"
    kb = FoundryIQ([ROOT / "knowledge", pizza, pizza / "agile"])
    if q:
        return [{"src": "knowledge", "citation": r["citation"], "text": r["snippet"][:240],
                 "score": r["score"]} for r in kb.retrieve(q, top_k=6)]
    return [{"src": "knowledge", "citation": f"{c['source']} § {c['heading']}",
             "text": c["text"][:160]} for c in kb.chunks[:20]]


def src_ontology(q=""):
    """Fabric IQ: entities, relationships, rules — the business meaning."""
    onto = json.loads((ROOT / "data" / "ontology.json").read_text(encoding="utf-8"))
    rows = []
    for c in onto["entities"]["certifications"]:
        text = (f"{c['id']} '{c['name']}' | skills: {', '.join(c['skills'])} | "
                f"{c['recommended_hours']}h, pass {c['pass_threshold']}% | "
                f"prerequisites: {c['prerequisites'] or 'none'}")
        if _hit(q, text):
            rows.append({"src": "ontology", "kind": "certification", "text": text})
    for r in onto["entities"]["roles"]:
        text = f"role {r['name']} requires: {', '.join(r['required_certifications'])}"
        if _hit(q, text):
            rows.append({"src": "ontology", "kind": "relationship", "text": text})
    for t in onto["entities"]["scope_tiers"]:
        text = f"Tier {t['tier']}: {t['meaning']} -> action: {t['action']}"
        if _hit(q, text):
            rows.append({"src": "ontology", "kind": "tier", "text": text})
    for rule in onto["rules"]:
        if _hit(q, rule["rule"], rule["id"]):
            rows.append({"src": "ontology", "kind": "rule", "text": f"{rule['id']}: {rule['rule']}"})
    return rows


def src_work(q=""):
    raw = json.loads((ROOT / "data" / "work_signals.json").read_text(encoding="utf-8"))
    rows = []
    for s in (raw["signals"] if isinstance(raw, dict) else raw):
        text = (f"{s['employee_id']}: {s['meeting_hours_per_week']}h meetings/wk, "
                f"{s['focus_hours_per_week']}h focus/wk, prefers {s['preferred_learning_slot']}"
                + (" [AT RISK: >20h meetings, rule R-2]" if s["meeting_hours_per_week"] > 20 else ""))
        if _hit(q, text):
            rows.append({"src": "work", "text": text})
    return rows


def src_learners(q=""):
    raw = json.loads((ROOT / "data" / "learners.json").read_text(encoding="utf-8"))
    rows = []
    for l in (raw["learners"] if isinstance(raw, dict) else raw):
        text = (f"{l['learner_id']} ({l.get('role','?')}) -> {l.get('certification','?')}: "
                f"practice {l.get('practice_score_avg','?')}%, {l.get('hours_studied','?')}h studied"
                + (f", status {l['status']}" if l.get("status") else ""))
        if _hit(q, text):
            rows.append({"src": "learners", "text": text})
    return rows


SOURCES = {"traces": src_traces, "decisions": src_decisions, "knowledge": src_knowledge,
           "ontology": src_ontology, "work": src_work, "learners": src_learners}


def explore(q="", source=None, agent=None, last=None):
    """Library entry point (used by the Command Center too)."""
    names = [source] if source and source in SOURCES else list(SOURCES)
    out = []
    for name in names:
        rows = SOURCES[name](q, agent) if name == "traces" else SOURCES[name](q)
        out.extend(rows)
    if last:
        out = out[-last:]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--source", choices=list(SOURCES), help="limit to one source")
    ap.add_argument("--agent")
    ap.add_argument("--last", type=int)
    ap.add_argument("--prompts", help="(legacy) search inside trace prompts")
    ap.add_argument("--decisions", help="(legacy) search the decision log")
    args = ap.parse_args()

    if args.decisions is not None:
        args.text, args.source = args.decisions, "decisions"
    if args.prompts is not None:
        args.text, args.source = args.prompts, "traces"

    rows = explore(args.text, args.source, args.agent, args.last)
    if not rows:
        print("No matches. Sources:", ", ".join(SOURCES))
        return
    cur = None
    for r in rows:
        if r["src"] != cur:
            cur = r["src"]
            print(f"\n═══ {cur.upper()} " + "═" * (50 - len(cur)))
        line = f"  {r.get('text','')}"
        if r.get("agent"):
            line = f"  [{r['ts']}] {r['agent']} ({r['model']}) → {r['text']}"
        if r.get("citation"):
            line = f"  [{r['citation']}] {r['text']}"
        print(line)
        if r.get("cites"):
            print(f"      cites: {'; '.join(r['cites'])}")
    print(f"\n({len(rows)} rows across {len(set(x['src'] for x in rows))} source(s))")


if __name__ == "__main__":
    main()
