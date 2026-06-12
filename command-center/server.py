#!/usr/bin/env python3
"""KISS Command Center — local dashboard server (stdlib only).

Three views (Assistant / Project Ops / Creative Studio) over the real Track 2
engine. Discovers every KISS project, switches between them, switches between
model tiers (Foundry / any local Ollama model / offline) at runtime.

Run:  python server.py   →  http://localhost:8765
"""

import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
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


def discover_projects():
    found = {}
    for base in [ROOT / "demo-project", ROOT / "creative-track1" / "output"]:
        if base.exists():
            for d in sorted(base.iterdir()):
                if d.is_dir() and (d / "PROJECT_STATE.md").exists():
                    found[d.name] = d
    return found


REGISTRY = HERE / "projects.json"


def load_registry():
    """User-added project folders (manual 'find my project'), persisted."""
    try:
        saved = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for name, p in saved.items():
        d = Path(p)
        if d.is_dir() and (d / "PROJECT_STATE.md").exists():
            out[name] = d
    return out


def save_registry():
    manual = {n: str(p) for n, p in PROJECTS.items()
              if ROOT not in p.resolve().parents}
    REGISTRY.write_text(json.dumps(manual, indent=2), encoding="utf-8")


PROJECTS = discover_projects()
PROJECTS.update(load_registry())
ACTIVE = "pizza-shop" if "pizza-shop" in PROJECTS else next(iter(PROJECTS))

print("Booting KISS engine …")
CTX = AgentContext(
    FoundryIQ([T2 / "knowledge"] + list(PROJECTS.values())
              + [p / "agile" for p in PROJECTS.values()]),
    FabricIQ(T2 / "data" / "ontology.json"),
    WorkIQ(T2 / "data" / "work_signals.json"),
    ModelClient(), TraceLogger("command-center"))
ORCH = KISSOrchestrator(CTX)
FOUNDRY_CLIENT = CTX.model._openai  # may be None
print("Projects:", ", ".join(PROJECTS), "| active:", ACTIVE, "| model:", CTX.model.mode)


def proj():
    return PROJECTS[ACTIVE]


def read(p):
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def vision_text():
    return read(proj() / "agile" / "PRODUCT_VISION.md") or read(proj() / "PRODUCT_VISION.md")


# ---- model ladder control -----------------------------------------------------
def ollama_models():
    try:
        with urllib.request.urlopen(CTX.model.ollama_url + "/api/tags", timeout=1.5) as r:
            return [m.get("name", "") for m in json.loads(r.read().decode()).get("models", [])]
    except Exception:
        return []


def model_options():
    opts = []
    if FOUNDRY_CLIENT:
        opts.append("foundry:" + CTX.model.deployment)
    opts += ["ollama:" + m for m in ollama_models()]
    opts.append("offline")
    return opts


def set_model(mode):
    if mode.startswith("foundry") and FOUNDRY_CLIENT:
        CTX.model._openai = FOUNDRY_CLIENT
        CTX.model._ollama = False
    elif mode.startswith("ollama:"):
        CTX.model._openai = None
        CTX.model.ollama_model = mode.split(":", 1)[1]
        CTX.model._ollama = True
    else:
        CTX.model._openai = None
        CTX.model._ollama = False
    return CTX.model.mode


# ---- panels --------------------------------------------------------------------
def board():
    todo = read(proj() / "TODO.md")
    def grab(mark):
        return re.findall(rf"^- \[{mark}\] ?(.+)", todo, re.M)[:10]
    return {"now": grab(" "), "done": grab("x"), "blocked": grab("~")}


def toggle_todo(line_text, done):
    f = proj() / "TODO.md"
    todo = read(f)
    src_mark, dst_mark = (" ", "x") if done else ("x", " ")
    old = f"- [{src_mark}] {line_text}"
    if old in todo:
        f.write_text(todo.replace(old, f"- [{dst_mark}] {line_text}", 1), encoding="utf-8")
        return True
    return False


READING_SETS = {
    "light  (small tweak)": ["PROJECT_STATE.md"],
    "medium (feature work)": ["PROJECT_STATE.md", "TODO.md", "DECISIONS.md"],
    "heavy  (architecture)": ["PROJECT_STATE.md", "TODO.md", "DECISIONS.md",
                              "RISK_POLICY.md", "agile/PRODUCT_VISION.md",
                              "PRODUCT_VISION.md", "ITERATION_LOG.md"],
}


def roi():
    rows = []
    for label, files in READING_SETS.items():
        chars = sum(len(read(proj() / f)) for f in files)
        rows.append({"set": label, "tokens": round(chars / 4)})
    total = round(sum(len(p.read_text(encoding="utf-8", errors="replace")) / 4
                      for p in proj().rglob("*.md")))
    return {"sets": rows, "total_tokens": total}


def health():
    warnings = []
    sw = len(read(proj() / "PROJECT_STATE.md").split())
    if sw > 400:
        warnings.append(f"PROJECT_STATE.md is {sw} words — snapshot becoming a changelog")
    le = len(re.findall(r"^#{2,3} ", read(proj() / "ITERATION_LOG.md"), re.M))
    if le > 20:
        warnings.append(f"ITERATION_LOG.md has {le} entries — archive older iterations")
    b = board()
    if len(b["now"]) > 8:
        warnings.append(f"{len(b['now'])} tasks in 'Now' — WIP limit exceeded")
    unv = len(re.findall(r"^- \[ \]", read(proj() / "PENDING_VERIFICATION.md"), re.M))
    if unv > 8:
        warnings.append(f"{unv} unverified items — verification-debt brake active")
    stale = len(re.findall(r"TBD|TODO:|\?\?\?", read(proj() / "DECISIONS.md")))
    if stale > 3:
        warnings.append(f"{stale} unresolved markers in DECISIONS.md — decision debt")
    return {"warnings": warnings, "ok": not warnings, "unverified": unv,
            "blocked": len(b["blocked"]), "now": len(b["now"]), "done": len(b["done"])}


def popsicle_seed():
    """Evidence-seeded Popsicle defaults (user can still adjust)."""
    h = health()
    total = max(1, h["now"] + h["done"])
    built = round(100 * h["done"] / total)
    control = max(20, 90 - 18 * h["blocked"])
    time_s = max(20, 90 - 15 * len(h["warnings"]))
    compute = max(20, 90 - 6 * max(0, roi()["total_tokens"] - 4000) // 1000)
    proud = round((built + control) / 2)
    return {"built": built, "control": control, "time": time_s,
            "compute": min(95, compute), "proud": proud,
            "evidence": f"{h['done']} done / {h['now']} open · {h['blocked']} blocked · "
                        f"{h['unverified']} unverified · {len(h['warnings'])} warnings"}


def next_best():
    h = health()
    if h["unverified"] > 8:
        mode, why = "Verification-first", f"{h['unverified']} unverified items — risk is growing faster than value"
        task = "Run a verification session: review PENDING_VERIFICATION.md top-to-bottom"
    elif h["blocked"] > 0:
        mode, why = "Decision-resolution", f"{h['blocked']} blocked item(s) are throttling the sprint"
        task = "Unblock: " + (board()["blocked"] or ["resolve the open blocker"])[0]
    elif h["now"] == 0:
        mode, why = "Planning", "the Now column is empty"
        task = "Pull the highest-value Later item into Now with acceptance criteria"
    else:
        mode, why = "Focused sprint", "no brakes triggered — ship the next smallest useful outcome"
        task = "Finish: " + board()["now"][0]
    later = read(proj() / "DECISIONS.md")
    tempt = re.search(r"Parked[^|]*\| ?(?:Feature: )?([^|\n]+)", later)
    return {"mode": mode, "why": why, "task": task,
            "tempting_but_wait": (tempt.group(1).strip() if tempt else "anything Tier 2/3")}


def memos(add=None):
    f = proj() / "MEMO.md"
    if add:
        if not f.exists():
            f.write_text("# Memo & Idea Inbox\n\n> Source of truth for: loose ideas "
                         "captured before they become tasks or decisions.\n\n", encoding="utf-8")
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(f"- [ ] {time.strftime('%Y-%m-%d')} | {add}\n")
    return re.findall(r"^- \[.\] ?(.+)", read(f), re.M)[-10:][::-1]


def latest_log():
    log = read(proj() / "ITERATION_LOG.md")
    parts = re.split(r"^(#{2,3} .+)$", log, flags=re.M)
    entries = ["".join(parts[i:i + 2]).strip()[:400] for i in range(1, len(parts), 2)]
    return entries[-3:][::-1]


def assets():
    out = []
    for d in [proj() / "assets", proj() / "vision"]:
        if d.exists():
            for f in sorted(d.iterdir()):
                if f.suffix in (".svg", ".png"):
                    out.append(f"/pfile?p={f.relative_to(proj()).as_posix()}")
    return out


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
        g = grounding[0] if grounding else None
        raw = (f"(offline tier) Closest grounded answer, from [{g['citation']}]: {g['snippet'][:300]}"
               if g else "(offline tier) Nothing in the knowledge base matches — try the scope gate.")
    CTX.tracer.log(agent="CommandCenterChat", model=CTX.model.mode,
                   prompt={"system": system, "user": message},
                   grounding=[g["citation"] for g in grounding],
                   output={"answer": raw}, extra={"project": ACTIVE})
    return {"answer": raw, "cites": [g["citation"] for g in grounding][:3]}


KISS_TEMPLATES = {
    "PROJECT_STATE.md": """# Project State — {name}

> Source of truth for: the CURRENT snapshot of this project. Never a changelog — dated history belongs in ITERATION_LOG.md.

**Sprint goal:** TBD — set your first sprint goal
**Status:** onboarding | **Created:** {date} by KISS studio upgrade

## Imported sources (pre-existing files, untouched)
{imports}

## Blockers
- None yet
""",
    "TODO.md": """# To Do — {name}

> Source of truth for: the real backlog. [ ] open · [x] done · [~] blocked.

## Now
- [ ] Review imported notes and set the sprint goal | light
- [ ] Fill PRODUCT_VISION.md tiers (what's v1, what's parked) | medium

## Later
""",
    "DECISIONS.md": """# Decisions — {name}

> Source of truth for: locked decisions and parked requests. Format: D-XXX | date | what | why | revisit trigger.

- **D-001** | {date} | Adopted KISS project memory (studio upgrade — existing files preserved, never deleted) | Why: durable agent memory + scope discipline | Revisit: never
""",
    "RISK_POLICY.md": """# Risk Policy — {name}

> Source of truth for: what an AI agent may do alone vs. what needs the owner.

- Tier 2/3 requests: capture in DECISIONS.md, don't build (default answer: "capture it, don't build it")
- STOP and ask before: deleting files, changing scope, anything irreversible
- Silence is never approval
""",
    "PRODUCT_VISION.md": """# Product Vision — {name}

## Scope Split

### In Scope for Tier 1 (build now)
- (fill in: the smallest version worth shipping)

### In Scope for Tier 2 (after Tier 1 ships)
- (capture, don't build)

### Out of Scope for Now
- (be honest)
""",
    "READ_FIRST.md": """# Read First — {name}

> Source of truth for: the MINIMUM files an agent must read per task type. Small tasks must not cost full-project context.

| Task type | Read only |
|---|---|
| Small tweak | PROJECT_STATE.md |
| Feature work | PROJECT_STATE.md, TODO.md, DECISIONS.md |
| Architecture / scope call | all KISS files + PRODUCT_VISION.md |
""",
    "PENDING_VERIFICATION.md": """# Pending Verification — {name}

> Source of truth for: built-but-not-tested work. At >8 open items, stop building and verify.
""",
}


def scaffold_kiss(d: Path):
    """Studio upgrade path: onboard an existing folder into KISS. Only creates
    missing files; never modifies or deletes anything that exists."""
    existing = sorted(f.name for f in d.glob("*.md"))[:12]
    imports = "\n".join("- " + n for n in existing) or "- (none found)"
    created = []
    for fname, tpl in KISS_TEMPLATES.items():
        target = d / fname
        if not target.exists():
            target.write_text(tpl.format(name=d.name, imports=imports,
                                         date=time.strftime("%Y-%m-%d")),
                              encoding="utf-8")
            created.append(fname)
    return created


def browse(path_str):
    """Server-side folder browser. Empty path = list drives (win) or / (posix)."""
    import string
    if not path_str:
        if sys.platform == "win32":
            import os
            drives = []
            for d in string.ascii_uppercase:
                for probe in (d + ":\\", d + ":/"):
                    if os.path.exists(probe):
                        drives.append(d + ":\\")
                        break
            return {"path": "", "parent": None,
                    "dirs": [{"name": d, "kiss": False} for d in drives]}
        path_str = "/"
    p = Path(path_str)
    if not p.is_dir():
        return {"error": "not a folder: " + path_str}
    dirs = []
    try:
        entries = sorted(p.iterdir())
    except PermissionError:
        return {"error": "permission denied: " + path_str}
    for d in entries:
        try:
            if d.is_dir() and not d.name.startswith((".", "$")) and d.name.lower() not in ("node_modules", "__pycache__"):
                dirs.append({"name": d.name,
                             "kiss": (d / "PROJECT_STATE.md").exists()})
        except (PermissionError, OSError):
            continue  # skip unreadable entries, keep the rest
    parent = str(p.parent) if p.parent != p else ("" if sys.platform == "win32" else None)
    return {"path": str(p), "parent": parent,
            "is_kiss": (p / "PROJECT_STATE.md").exists(), "dirs": dirs[:200]}


def board_to_ics():
    """Export the active project's open + blocked tasks as calendar events
    (.ics — opens in Outlook, Google, or Apple Calendar). Zero-auth bridge to
    the calendar; live Graph sync is parked (D-H07/D-H10)."""
    import datetime
    b = board()
    day = datetime.date.today() + datetime.timedelta(days=1)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//KISS Studio//Command Center//EN"]
    n = 0
    for kind, items in (("TODO", b["now"]), ("BLOCKED", b["blocked"])):
        for t in items:
            d = day + datetime.timedelta(days=n // 3)  # ~3 tasks per day
            title = (("[BLOCKED] " if kind == "BLOCKED" else "") + t.split("|")[0].strip())[:120]
            lines += ["BEGIN:VEVENT",
                      f"UID:kiss-{ACTIVE}-{n}@kiss.local",
                      "DTSTAMP:" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
                      "DTSTART;VALUE=DATE:" + d.strftime("%Y%m%d"),
                      "SUMMARY:" + title.replace(",", "\\,"),
                      "DESCRIPTION:KISS project " + ACTIVE + " - from TODO.md",
                      "END:VEVENT"]
            n += 1
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


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
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        routes = {
            "/api/board": board, "/api/roi": roi, "/api/health": health,
            "/api/popsicle": popsicle_seed, "/api/nextbest": next_best,
            "/api/log": latest_log, "/api/assets": assets,
            "/api/memo": lambda: memos(),
        }
        if u.path == "/":
            self._file(HERE / "index.html", "text/html; charset=utf-8")
        elif u.path.startswith("/assets/"):
            f = (HERE / u.path.lstrip("/")).resolve()
            if f.is_file() and HERE in f.parents:
                self._file(f, "image/png")
            else:
                self._json({"error": "not found"}, 404)
        elif u.path == "/pfile":
            f = (proj() / qs.get("p", [""])[0]).resolve()
            if f.is_file() and proj().resolve() in f.parents and f.suffix in (".svg", ".png"):
                self._file(f, "image/svg+xml" if f.suffix == ".svg" else "image/png")
            else:
                self._json({"error": "not found"}, 404)
        elif u.path == "/api/status":
            self._json({"model": CTX.model.mode, "models": model_options(),
                        "chunks": len(CTX.foundry_iq.chunks),
                        "trace_file": CTX.tracer.path.name,
                        "projects": list(PROJECTS), "active": ACTIVE})
        elif u.path == "/api/browse":
            self._json(browse(qs.get("path", [""])[0]))
        elif u.path == "/api/calendar.ics":
            body = board_to_ics().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/calendar; charset=utf-8")
            self.send_header("Content-Disposition",
                             f'attachment; filename="kiss-{ACTIVE}.ics"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif u.path == "/api/traces":
            self._json(traces(qs.get("q", [""])[0]))
        elif u.path == "/api/vision":
            self._json({"svg": read(proj() / "vision" / "vision_board.svg")})
        elif u.path in routes:
            self._json(routes[u.path]())
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        global ACTIVE
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/add-project":
            d = Path(data.get("path", "").strip().strip('"'))
            if not d.is_dir():
                self._json({"error": "Folder not found: " + str(d)}, 400)
            elif not (d / "PROJECT_STATE.md").exists():
                mds = sorted(f.name for f in d.glob("*.md"))[:8]
                self._json({"offer_init": True, "path": str(d),
                            "found_md": mds,
                            "message": "No KISS files here yet ("
                            + (", ".join(mds) if mds else "no .md files")
                            + " found). Initialize this folder as a KISS project? "
                            "Existing files are preserved and listed as imported "
                            "sources - nothing is modified or deleted."})
            else:
                name = d.name
                while name in PROJECTS and PROJECTS[name] != d:
                    name += "_2"
                PROJECTS[name] = d
                save_registry()
                for f in sorted(d.rglob("*.md")):
                    CTX.foundry_iq._index_file(f)  # ground the new project's knowledge
                ACTIVE = name
                CTX.tracer.log(agent="CommandCenter", phase="add_project",
                               output={"name": name, "path": str(d)})
                self._json({"active": name, "projects": list(PROJECTS)})
        elif self.path == "/api/init-project":
            d = Path(data.get("path", "").strip().strip('"'))
            if not d.is_dir():
                self._json({"error": "Folder not found: " + str(d)}, 400)
            else:
                created = scaffold_kiss(d)
                name = d.name
                while name in PROJECTS and PROJECTS[name] != d:
                    name += "_2"
                PROJECTS[name] = d
                save_registry()
                for f in sorted(d.rglob("*.md")):
                    CTX.foundry_iq._index_file(f)
                ACTIVE = name
                CTX.tracer.log(agent="CommandCenter", phase="init_project",
                               output={"name": name, "created": created})
                self._json({"active": name, "created": created,
                            "projects": list(PROJECTS)})
        elif self.path == "/api/project":
            name = data.get("project", "")
            if name in PROJECTS:
                ACTIVE = name
                self._json({"active": ACTIVE})
            else:
                self._json({"error": "unknown project"}, 400)
        elif self.path == "/api/model":
            self._json({"model": set_model(data.get("mode", "offline"))})
        elif self.path == "/api/scope":
            r = ORCH.scope_request(data.get("request", ""), vision_text())
            self._json({"verdict": r.get("verdict"), "tier": r.get("tier"),
                        "answer": r.get("answer"), "critic": r["critic"]["verdict"],
                        "project": ACTIVE})
        elif self.path == "/api/chat":
            self._json(chat(data.get("message", "")))
        elif self.path == "/api/memo":
            self._json({"memos": memos(add=data.get("text", "").strip() or None)})
        elif self.path == "/api/todo":
            ok = toggle_todo(data.get("line", ""), data.get("done", True))
            self._json({"ok": ok, **board()})
        elif self.path == "/api/visualize":
            import os
            env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
            try:
                r = subprocess.run([sys.executable, str(ROOT / "creative-track1" / "visualize.py"),
                                    str(proj())], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace",
                                   timeout=180, env=env,
                                   cwd=str(ROOT / "creative-track1"))
                out = (r.stdout or "") + (r.stderr or "")
                ok = r.returncode == 0
            except Exception as exc:
                out, ok = f"{type(exc).__name__}: {exc}", False
            print(("[visualize OK]\n" if ok else "[visualize FAILED]\n") + out[-800:], flush=True)
            self._json({"ok": ok, "out": out[-800:]})
        else:
            self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    print("KISS Command Center → http://localhost:8765")
    HTTPServer(("127.0.0.1", 8765), H).serve_forever()
