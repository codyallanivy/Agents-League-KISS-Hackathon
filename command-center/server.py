#!/usr/bin/env python3
"""KISS Command Center — local dashboard server (stdlib only).

Wraps the real Track 2 reasoning engine behind a tiny HTTP API and serves the
single-page UI. Discovers every KISS project in the repo and lets the UI
switch between them; scope checks always run against the ACTIVE project's
PRODUCT_VISION.md.

Run:  python server.py   →  http://localhost:8765
"""

import json
import re
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "foundry-track2"))

from agents.base_agent import AgentContext, ModelClient, TraceLogger  # noqa: E402
from agents.orchestrator import KISSOrchestrator                      # noqa: E402
from iq.foundry_iq import FoundryIQ                                   # noqa: E402
from iq.fabric_iq import FabricIQ                                     # noqa: E402
from iq.work_iq import WorkIQ                                         # noqa: E402

T2 = ROOT / "foundry-track2"


# ---- project discovery -------------------------------------------------------
def discover_projects():
    found = {}
    for base in [ROOT / "demo-project", ROOT / "creative-track1" / "output"]:
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and (d / "PROJECT_STATE.md").exists():
                found[d.name] = d
    return found


PROJECTS = discover_projects()
ACTIVE = "pizza-shop" if "pizza-shop" in PROJECTS else next(iter(PROJECTS))

print("Booting KISS engine …")
CTX = AgentContext(
    FoundryIQ([T2 / "knowledge"] + [p for p in PROJECTS.values()]
              + [p / "agile" for p in PROJECTS.values()]),
    FabricIQ(T2 / "data" / "ontology.json"),
    WorkIQ(T2 / "data" / "work_signals.json"),
    ModelClient(), TraceLogger("command-center"))
ORCH = KISSOrchestrator(CTX)
print("Projects:", ", ".join(PROJECTS), "| active:", ACTIVE, "| model:", CTX.model.mode)


def proj():
    return PROJECTS[ACTIVE]


def read(p):
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def vision_text():
    return read(proj() / "agile" / "PRODUCT_VISION.md") or read(proj() / "PRODUCT_VISION.md")


def board():
    todo = read(proj() / "TODO.md")
    return {"now": re.findall(r"^- \[ \] ?(.+)", todo, re.M)[:8],
            "done": re.findall(r"^- \[x\] ?(.+)", todo, re.M)[:8],
            "blocked": re.findall(r"^- \[~\] ?(.+)", todo, re.M)[:8]}


# ---- Pro features: Context ROI + bloat health --------------------------------
READING_SETS = {
    "light  (small tweak)": ["PROJECT_STATE.md"],
    "medium (feature work)": ["PROJECT_STATE.md", "TODO.md", "DECISIONS.md"],
    "heavy  (architecture)": ["PROJECT_STATE.md", "TODO.md", "DECISIONS.md",
                              "RISK_POLICY.md", "agile/PRODUCT_VISION.md",
                              "PRODUCT_VISION.md", "ITERATION_LOG.md"],
}


def roi():
    """Pre-spend context cost: estimated tokens of each task type's minimum
    reading set (chars/4 heuristic). Planning tool, not an accountant."""
    rows = []
    for label, files in READING_SETS.items():
        chars = sum(len(read(proj() / f)) for f in files)
        rows.append({"set": label, "files": sum(1 for f in files if (proj() / f).exists()),
                     "tokens": round(chars / 4)})
    return rows


def health():
    warnings = []
    state_words = len(read(proj() / "PROJECT_STATE.md").split())
    if state_words > 400:
        warnings.append(f"PROJECT_STATE.md is {state_words} words — snapshot is becoming a changelog (move history to ITERATION_LOG.md)")
    log_entries = len(re.findall(r"^#{2,3} ", read(proj() / "ITERATION_LOG.md"), re.M))
    if log_entries > 20:
        warnings.append(f"ITERATION_LOG.md has {log_entries} entries — consider archiving older iterations")
    now_n = len(board()["now"])
    if now_n > 8:
        warnings.append(f"{now_n} tasks in 'Now' — WIP limit exceeded, move some to Later")
    unverified = len(re.findall(r"^- \[ \]", read(proj() / "PENDING_VERIFICATION.md"), re.M))
    if unverified > 8:
        warnings.append(f"{unverified} unverified items — verification-debt brake: stop building, start verifying")
    return {"warnings": warnings, "ok": not warnings}


def traces(q=""):
    steps = []
    for f in sorted((T2 / "traces").glob("run-*.jsonl"))[-12:]:
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                s = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not q or q.lower() in json.dumps(s).lower():
                steps.append({"ts": s.get("ts"), "agent": s.get("agent"),
                              "model": s.get("model", "-"),
                              "answer": (s.get("output", {}).get("answer")
                                         or json.dumps(s.get("output", {}))[:160])[:240],
                              "cites": (s.get("grounding") or [])[:3]})
    return steps[-30:][::-1]


def chat(message):
    grounding = CTX.foundry_iq.retrieve(message)
    system = ("You are the KISS Agile coach. Answer from the cited project knowledge; "
              "protect scope; be concise and warm. Cite sources in [brackets].")
    cites = "\n\n".join(f"[{g['citation']}]\n{g['snippet']}" for g in grounding) or "(none)"
    raw = CTX.model.complete(system, f"QUESTION: {message}\n\nKNOWLEDGE:\n{cites}")
    if raw is None:
        if grounding:
            g = grounding[0]
            raw = (f"(offline tier — install Ollama for real chat)  Closest grounded answer, "
                   f"from [{g['citation']}]: {g['snippet'][:300]}")
        else:
            raw = "(offline tier) Nothing in the knowledge base matches that — try the scope gate or traces."
    CTX.tracer.log(agent="CommandCenterChat", model=CTX.model.mode,
                   prompt={"system": system, "user": message},
                   grounding=[g["citation"] for g in grounding],
                   output={"answer": raw}, extra={"project": ACTIVE})
    return {"answer": raw, "cites": [g["citation"] for g in grounding][:3]}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path, ctype):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global ACTIVE
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        if u.path == "/":
            self._file(HERE / "index.html", "text/html; charset=utf-8")
        elif u.path.startswith("/assets/"):
            f = (HERE / u.path.lstrip("/")).resolve()
            if f.is_file() and HERE in f.parents:
                self._file(f, "image/png")
            else:
                self._json({"error": "not found"}, 404)
        elif u.path == "/api/status":
            self._json({"model": CTX.model.mode, "chunks": len(CTX.foundry_iq.chunks),
                        "trace_file": CTX.tracer.path.name,
                        "projects": list(PROJECTS), "active": ACTIVE})
        elif u.path == "/api/board":
            self._json(board())
        elif u.path == "/api/roi":
            self._json(roi())
        elif u.path == "/api/health":
            self._json(health())
        elif u.path == "/api/traces":
            self._json(traces(qs.get("q", [""])[0]))
        elif u.path == "/api/vision":
            svg = proj() / "vision" / "vision_board.svg"
            self._json({"svg": read(svg)})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        global ACTIVE
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/project":
            name = data.get("project", "")
            if name in PROJECTS:
                ACTIVE = name
                CTX.tracer.log(agent="CommandCenter", phase="switch_project",
                               output={"active": ACTIVE})
                self._json({"active": ACTIVE})
            else:
                self._json({"error": "unknown project"}, 400)
        elif self.path == "/api/scope":
            r = ORCH.scope_request(data.get("request", ""), vision_text())
            self._json({"verdict": r.get("verdict"), "tier": r.get("tier"),
                        "answer": r.get("answer"), "critic": r["critic"]["verdict"],
                        "cites": r.get("citations", [])[:3], "project": ACTIVE})
        elif self.path == "/api/chat":
            self._json(chat(data.get("message", "")))
        else:
            self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    print("KISS Command Center → http://localhost:8765")
    HTTPServer(("127.0.0.1", 8765), H).serve_forever()
