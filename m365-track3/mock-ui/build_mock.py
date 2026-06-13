#!/usr/bin/env python3
"""Builds teams-mock.html — a static mock of the KISS Governance Agent in
M365 Copilot / Teams, rendered from REAL Track 2 outputs (latest traces +
learner data). Re-run after each Track 2 run to refresh the demo."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
T2 = HERE.parent.parent / "foundry-track2"


def latest_scope_step():
    steps = []
    for f in sorted((T2 / "traces").glob("run-*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                s = json.loads(line)
            except json.JSONDecodeError:
                continue
            if s.get("agent") == "AssessmentAgent" and s.get("extra", {}).get("feature_request"):
                steps.append(s)
    return steps[-1] if steps else None


def team_stats():
    raw = json.loads((T2 / "data" / "learners.json").read_text(encoding="utf-8"))
    learners = raw["learners"] if isinstance(raw, dict) else raw
    onto = json.loads((T2 / "data" / "ontology.json").read_text(encoding="utf-8"))
    certs = {c["id"]: c for c in onto["entities"]["certifications"]}
    sigs = json.loads((T2 / "data" / "work_signals.json").read_text(encoding="utf-8"))
    sigs = {s["employee_id"]: s for s in (sigs["signals"] if isinstance(sigs, dict) else sigs)}
    ready = risk = 0
    for l in learners:
        c = certs[l["certification"]]
        if l["practice_score_avg"] >= c["pass_threshold"] and l["hours_studied"] >= 0.75 * c["recommended_hours"]:
            ready += 1
        s = sigs.get(l["learner_id"])
        if s and s["meeting_hours_per_week"] > 20:
            risk += 1
    return {"total": len(learners), "ready": ready, "studying": len(learners) - ready, "risk": risk}


scope = latest_scope_step() or {}
out = scope.get("output", {})
stats = team_stats()
data = {
    "scope": {
        "feature": scope.get("extra", {}).get("feature_request", "Add blockchain payment integration"),
        "tier": out.get("tier", 3),
        "verdict": out.get("verdict", "BLOCK"),
        "answer": out.get("answer", ""),
        "citations": out.get("citations", []),
        "run_id": scope.get("run_id", "-"),
        "ts": scope.get("ts", "-"),
    },
    "team": stats,
}

template = (HERE / "template.html").read_text(encoding="utf-8")
html = template.replace("/*__DATA__*/", "const DATA = " + json.dumps(data, ensure_ascii=False) + ";")
(HERE / "teams-mock.html").write_text(html, encoding="utf-8")
print("built teams-mock.html from trace", data["scope"]["run_id"])
