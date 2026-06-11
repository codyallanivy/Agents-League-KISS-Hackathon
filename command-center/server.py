#!/usr/bin/env python3
"""KISS Command Center — local dashboard server (stdlib only).

Wraps the real Track 2 reasoning engine behind a tiny HTTP API and serves the
single-page UI. The model ladder (Foundry → Ollama → offline) is whatever the
engine detects — the badge in the UI tells you which brain is on.

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
sys.path.insert(0, str(ROOT / "creative-track1"))

from agents.base_agent import AgentContext, ModelClient, TraceLogger  # noqa: E402
from agents.orchestrator import KISSOrchestrator                      # noqa: E402
from iq.foundry_iq import FoundryIQ                                   # noqa: E402
from iq.fabric_iq import FabricIQ                                     # noqa: E402
from iq.work_iq import WorkIQ                                         # noqa: E402

T2 = ROOT / "foundry-track2"
PIZZA = ROOT / "demo-project" / "pizza-shop"

print("Booting KISS engine …")
CTX = AgentContext(
    FoundryIQ([T2 / "knowledge", PIZZA, PIZZA / "agile"]),
    FabricIQ(T2 / "data" / "ontology.json"),
    WorkIQ(T2 / "data" / "work_signals.json"),
    ModelClient(), TraceLogger("command-center"))
ORCH = KISSOrchestrator(CTX)
VISION = (PIZZA / "agile" / "PRODUCT_VISION.md").read_text(encoding="utf-8")
print("Model tier:", CTX.model.mode)


def board():
    todo = (PIZZA / "TODO.md").read_text(encoding="utf-8") if (PIZZA / "TODO.md").exists() else ""
    return {
        "now": re.findall(r"^- \[ \] ?(.+)", todo, re.M)[:8],
        "done": re.findall(r"^- \[x\] ?(.+)", todo, re.M)[:8],
        "blocked": re.findall(r"^- \[~\] ?(.+)", todo, re.M)[:8],
    }


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
                   output={"answer": raw})
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

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        if u.path == "/":
            body = (HERE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif u.path == "/api/status":
            self._json({"model": CTX.model.mode,
                        "chunks": len(CTX.foundry_iq.chunks),
                        "trace_file": CTX.tracer.path.name})
        elif u.path == "/api/board":
            self._json(board())
        elif u.path == "/api/traces":
            self._json(traces(qs.get("q", [""])[0]))
        elif u.path == "/api/vision":
            svg = PIZZA / "vision" / "vision_board.svg"
            self._json({"svg": svg.read_text(encoding="utf-8") if svg.exists() else ""})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/scope":
            r = ORCH.scope_request(data.get("request", ""), VISION)
            self._json({"verdict": r.get("verdict"), "tier": r.get("tier"),
                        "answer": r.get("answer"), "critic": r["critic"]["verdict"],
                        "cites": r.get("citations", [])[:3]})
        elif self.path == "/api/chat":
            self._json(chat(data.get("message", "")))
        else:
            self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    print("KISS Command Center → http://localhost:8765")
    HTTPServer(("127.0.0.1", 8765), H).serve_forever()
