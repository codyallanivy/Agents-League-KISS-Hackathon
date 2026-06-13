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
sys.path.insert(0, str(ROOT / "creative-track1"))

from agents.base_agent import AgentContext, ModelClient, TraceLogger  # noqa: E402
from agents.orchestrator import KISSOrchestrator                      # noqa: E402
from iq.foundry_iq import FoundryIQ                                   # noqa: E402
from iq.fabric_iq import FabricIQ                                     # noqa: E402
from iq.work_iq import WorkIQ                                         # noqa: E402

T2 = ROOT / "foundry-track2"
FANTASY_TEMPLATE = ROOT / "creative-track1" / "fantasy-template"
LEGACY_FANTASY_MARKERS = (
    "current snapshot of the campaign build",
    "playable 3-session campaign",
    "named npcs",
    "tabletop-rpg",
    "drowned shrine",
    "greyharbor",
)


def path_is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def looks_like_legacy_fantasy_project(d: Path) -> bool:
    """Detect old generated campaign outputs before the intake became neutral."""
    if (d / "CREATION.md").exists():
        return False
    hay = []
    for name in ("PROJECT_STATE.md", "PRODUCT_VISION.md", "CAMPAIGN.md"):
        p = d / name
        if p.exists():
            hay.append(p.read_text(encoding="utf-8", errors="replace")[:4000].lower())
    joined = "\n".join(hay)
    return any(marker in joined for marker in LEGACY_FANTASY_MARKERS)


def is_fantasy(d: Path) -> bool:
    """A dir flagged as isolated fantasy-template output. These are never
    discovered or indexed, so the optional fantasy template cannot influence
    any other project's planning or grounded output."""
    return (
        (d / ".fantasy").exists()
        or path_is_under(d, FANTASY_TEMPLATE)
        or looks_like_legacy_fantasy_project(d)
    )


def fantasy_citation(citation: str) -> bool:
    """Block stale in-memory citations from old fantasy/chunk indexes."""
    c = (citation or "").lower()
    return any(marker in c for marker in (
        "ember-tides/",
        "ember-roast/",
        "pizza-website/",
        "fantasy-template/",
    ))


def fantasy_hit(hit: dict) -> bool:
    c = (hit.get("citation") or "").lower()
    if fantasy_citation(c):
        return True
    body = f"{c}\n{hit.get('snippet', '')}".lower()
    return "campaign.md" in c and any(marker in body for marker in LEGACY_FANTASY_MARKERS)


def safe_index_project(d: Path):
    if is_fantasy(d):
        return 0
    count = 0
    for f in sorted(d.rglob("*.md")):
        if path_is_under(f, FANTASY_TEMPLATE):
            continue
        CTX.foundry_iq._index_file(f)
        count += 1
    return count


def output_project_dir(seed: str) -> Path:
    slug = re.sub(r"[^a-z0-9 _-]", "", (seed or "new project").lower()).strip()
    slug = re.sub(r"\s+", "-", slug) or "new-project"
    base = ROOT / "creative-track1" / "output" / slug
    if not base.exists() or not is_fantasy(base):
        return base
    n = 2
    while True:
        candidate = ROOT / "creative-track1" / "output" / f"{slug}-{n}"
        if not candidate.exists():
            return candidate
        n += 1


def discover_projects():
    found = {}
    for base in [ROOT / "demo-project", ROOT / "creative-track1" / "output"]:
        if base.exists():
            for d in sorted(base.iterdir()):
                if d.is_dir() and (d / "PROJECT_STATE.md").exists() and not is_fantasy(d):
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
        if d.is_dir() and (d / "PROJECT_STATE.md").exists() and not is_fantasy(d):
            out[name] = d
    return out


def save_registry():
    manual = {n: str(p) for n, p in PROJECTS.items()
              if ROOT not in p.resolve().parents}
    REGISTRY.write_text(json.dumps(manual, indent=2), encoding="utf-8")


PROJECTS = discover_projects()
PROJECTS.update(load_registry())
ACTIVE = next((p for p in ("creator-launch", "pizza-shop") if p in PROJECTS), next(iter(PROJECTS)))

try:
    from dotenv import load_dotenv
    load_dotenv(T2 / ".env")
except ImportError:
    pass

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


def creation_doc(d=None):
    """The project's primary creation document. New projects use CREATION.md;
    older demo projects may still use CAMPAIGN.md (read-compatible)."""
    d = d or proj()
    return (d / "CREATION.md") if (d / "CREATION.md").exists() else (d / "CAMPAIGN.md")


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


def retrieve_for_mode(query, mode="project", top_k=4):
    """Project-aware retrieval: keep one project's memory from contaminating
    another project's reasoning. Always allows the ACTIVE project's own files
    plus shared KISS method knowledge; other projects never bleed in. (Citations
    from FoundryIQ are prefixed with the project folder, so the ACTIVE + "/" gate
    is exact.) This is what stops, e.g., creative content surfacing inside an
    unrelated project's planning answers."""
    results = [g for g in CTX.foundry_iq.retrieve(query, top_k=25)
               if not fantasy_hit(g)]
    if mode == "global":
        return results[:top_k]
    core = ["kiss_certification_guide.md", "context_health_policy.md"]
    allowed = [ACTIVE + "/"] + core
    filtered = [g for g in results if any(a in g.get("citation", "") for a in allowed)]
    # No global fallback: if nothing in the ACTIVE project (or shared method docs)
    # matches, return nothing rather than leaking another project's memory into
    # the answer. This is what kept unrelated questions reaching for other projects.
    return filtered[:top_k]


def chat(message, file_context="", mode="project"):
    grounding = retrieve_for_mode(message, mode)
    if file_context:
        # project-only grounding: drop chunks from other projects/domains so
        # e.g. a coffee brand never inherits fantasy-campaign flavor
        own = [g for g in grounding if g["citation"].startswith(ACTIVE + "/")]
        grounding = [{"citation": f"{ACTIVE} project files (live)",
                      "snippet": file_context[:1200]}] + own[:3]
    if mode == "assistant":
        # A real general assistant: answer ANY question from the model's own
        # knowledge. Project notes are optional context, attached only when they
        # actually match the active project — never forced into unrelated answers,
        # and never another project's content.
        system = ("You are a helpful, knowledgeable general assistant. Answer the "
                  "user's question directly and accurately from your own knowledge. "
                  "Optional project notes may appear below; use them ONLY if the "
                  "question is clearly about the user's active project, otherwise "
                  "ignore them entirely and just answer normally. Never pad an "
                  "unrelated answer with project references. Be concise and warm.")
        notes = ("\n\n".join(f"[{g['citation']}]\n{g['snippet']}" for g in grounding)
                 or "(no project notes apply — answer from general knowledge)")
        raw = CTX.model.complete(system, f"QUESTION: {message}\n\nOPTIONAL PROJECT NOTES:\n{notes}")
        if raw is None:
            raw = ("(offline tier) General questions need a model tier — switch on "
                   "Foundry or Ollama in the top bar. I can still answer questions "
                   "about your active project offline.")
        CTX.tracer.log(agent="Assistant", model=CTX.model.mode,
                       prompt={"system": "assistant", "user": message},
                       grounding=[g["citation"] for g in grounding],
                       output={"answer": raw}, extra={"project": ACTIVE})
        # only surface citations when project notes were actually relevant/used
        return {"answer": raw, "cites": [g["citation"] for g in grounding][:3]}
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


def art_direction(project_dir=None):
    """Read the project's own files to infer art direction: tone -> palette,
    goal -> subject, brand voice -> style words. The art inherits the project."""
    d = project_dir or proj()
    text = " ".join(read(d / f) for f in
                    ("PROJECT_STATE.md", "PRODUCT_VISION.md", "BRAND_VOICE.md",
                     "agile/PRODUCT_VISION.md")).lower()
    # Neutral, domain-agnostic tone -> palette mapping (see intake_studio.PALETTES).
    if any(w in text for w in ("grim", "dark", "noir", "premium", "luxury", "bold", "serious")):
        tone = "bold"
    elif any(w in text for w in ("warm", "cozy", "friendly", "playful", "fun", "homey")):
        tone = "warm"
    elif any(w in text for w in ("calm", "minimal", "clinical", "modern", "tech")):
        tone = "calm"
    else:
        tone = "clean"
    goal = (re.search(r"(?:sprint goal|goal|vision)[:*\s]+(.+)", read(d / "PROJECT_STATE.md"),
                      re.I) or [None, d.name])[1].strip()[:90]
    voice = read(d / "BRAND_VOICE.md")[:200].replace("\n", " ")
    return {"tone": tone, "goal": goal, "voice": voice}


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
        self.send_header("Access-Control-Allow-Origin", "*")
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

    def _redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

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
        elif u.path == "/builder":
            self._file(HERE / "builder-studio-prototype.html", "text/html; charset=utf-8")
        elif u.path == "/builder-iq":
            self._redirect("/builder")
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
        elif u.path == "/api/query":
            from query import explore
            rows = explore(qs.get("q", [""])[0],
                           qs.get("source", [None])[0] or None)
            self._json(rows[-60:])
        elif u.path == "/api/vision":
            self._json({"svg": read(proj() / "vision" / "vision_board.svg")})
        elif u.path in routes:
            self._json(routes[u.path]())
        else:
            self._json({"error": "not found"}, 404)

    def _survey_questions(self, data):
            idea = data.get("idea", "").strip()
            qs = None
            if CTX.model.mode != "offline" and idea:
                raw = CTX.model.complete(
                    "You design project-intake surveys. Given an idea, return EXACTLY a "
                    "JSON array of 5 short intake questions tailored to that idea — "
                    "covering: a name/seed, the look/feel or tone, the single must-have "
                    "for v1, what is explicitly out of scope, and who it is for. "
                    'Format: [{"q": "...", "placeholder": "..."}]. JSON only.',
                    "IDEA: " + idea[:400])
                try:
                    s = raw[raw.index("["):raw.rindex("]") + 1]
                    qs = json.loads(s)[:5]
                    qs = [q for q in qs if isinstance(q, dict) and q.get("q")]
                except Exception:
                    qs = None
            if not qs:
                qs = [
                    {"q": "What should we call it? (a name or a few seed words)", "placeholder": "name / seed words"},
                    {"q": "What's the look and feel? (tone, mood, style)", "placeholder": "e.g. warm and playful / dark and serious"},
                    {"q": "The ONE thing v1 must have?", "placeholder": "the must-have"},
                    {"q": "What is explicitly OUT of scope for now?", "placeholder": "the off-limits"},
                    {"q": "Who is it for?", "placeholder": "audience"},
                ]
            self._json({"questions": qs, "model": CTX.model.mode})

    def do_POST(self):
        global ACTIVE, PROJECTS
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/add-project":
            d = Path(data.get("path", "").strip().strip('"'))
            if not d.is_dir():
                self._json({"error": "Folder not found: " + str(d)}, 400)
            elif is_fantasy(d):
                self._json({"error": "That folder is isolated fantasy-template output, "
                            "so it is not indexed into normal projects. Use start.bat "
                            "option 3 when you want the fantasy template on purpose."}, 400)
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
                safe_index_project(d)  # ground the new project's knowledge
                ACTIVE = name
                CTX.tracer.log(agent="CommandCenter", phase="add_project",
                               output={"name": name, "path": str(d)})
                self._json({"active": name, "projects": list(PROJECTS)})
        elif self.path == "/api/init-project":
            d = Path(data.get("path", "").strip().strip('"'))
            if not d.is_dir():
                self._json({"error": "Folder not found: " + str(d)}, 400)
            elif is_fantasy(d):
                self._json({"error": "That folder is reserved for isolated fantasy-template "
                            "output and cannot be initialized as a normal KISS project."}, 400)
            else:
                created = scaffold_kiss(d)
                name = d.name
                while name in PROJECTS and PROJECTS[name] != d:
                    name += "_2"
                PROJECTS[name] = d
                save_registry()
                safe_index_project(d)
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
            self._json(chat(data.get("message", ""), mode=data.get("mode", "project")))
        elif self.path == "/api/memo":
            self._json({"memos": memos(add=data.get("text", "").strip() or None)})
        elif self.path == "/api/todo":
            ok = toggle_todo(data.get("line", ""), data.get("done", True))
            self._json({"ok": ok, **board()})
        elif self.path == "/api/new-project":
            name = re.sub(r"[^a-zA-Z0-9 _-]", "", data.get("name", "")).strip()
            if not name:
                self._json({"error": "give the project a name"}, 400)
            else:
                d = ROOT / "creative-track1" / "output" / name.lower().replace(" ", "-")
                if d.exists() and is_fantasy(d):
                    self._json({"error": "That project name points at isolated fantasy-template "
                                "output. Choose a fresh project name for the neutral builder."}, 400)
                    return
                d.mkdir(parents=True, exist_ok=True)
                created = scaffold_kiss(d)
                PROJECTS = globals()["PROJECTS"]
                PROJECTS[d.name] = d
                safe_index_project(d)
                ACTIVE = d.name
                globals()["ACTIVE"] = d.name
                self._json({"active": d.name, "created": created, "projects": list(PROJECTS)})
        elif self.path == "/api/add-asset":
            kind = data.get("kind", "cover").strip().lower()
            prompt_txt = data.get("prompt", "").strip() or kind
            from asset_governor import AssetGovernor as _AG
            import intake_studio as ist
            kind = kind if kind in ist.ASSET_KINDS else "cover"
            gov = _AG(proj())
            d = gov.check(kind, prompt_txt)
            if d["verdict"] == "BLOCK":
                gov.park(kind, prompt_txt, d["reasons"])
                self._json({"error": "Governor: BLOCK — " + "; ".join(d["reasons"])}, 400)
            else:
                ad = art_direction()
                pal = ist.palette_for(ad["tone"])
                (proj() / "assets").mkdir(exist_ok=True)
                n = 1
                while (proj() / "assets" / f"{kind}-{n}.svg").exists():
                    n += 1
                p = proj() / "assets" / f"{kind}-{n}.svg"
                ist.svg_asset(kind, prompt_txt[:36], pal, p, seed=ACTIVE + prompt_txt)
                gov.record_generation(kind, p.name, d["estimated_cost_usd"])
                self._json({"ok": True, "file": p.name, "verdict": d["verdict"],
                            "note": d["reasons"][0] if d["reasons"] else ""})
        elif self.path == "/api/verify-assets":
            pv = proj() / "PENDING_VERIFICATION.md"
            n = 0
            if pv.exists():
                txt = pv.read_text(encoding="utf-8")
                n = txt.count("- [ ]")
                pv.write_text(txt.replace("- [ ]", "- [x]"), encoding="utf-8")
                with open(proj() / "ITERATION_LOG.md", "a", encoding="utf-8") as fh:
                    fh.write(f"\n## {time.strftime('%Y-%m-%d %H:%M')} — verification session\n"
                             f"{n} assets reviewed and marked verified via gallery.\n")
            self._json({"verified": n})
        elif self.path == "/api/prefer":
            pref = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "prompt": data.get("prompt", ""),
                    "chosen": data.get("chosen", {}),
                    "rejected": data.get("rejected", []),
                    "project": ACTIVE}
            pf = T2 / "traces" / "preferences.jsonl"
            with open(pf, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(pref, ensure_ascii=False) + "\n")
            count = sum(1 for _ in open(pf, encoding="utf-8"))
            self._json({"ok": True, "dataset_pairs": count})
        elif self.path == "/api/compare":
            msg = data.get("message", "").strip()
            modes = data.get("modes") or model_options()
            results, original = [], CTX.model.mode
            for m in modes[:3]:
                set_model(m)
                t0 = time.time()
                c = chat(msg)
                results.append({"mode": CTX.model.mode,
                                "answer": (c["answer"] or "")[:900],
                                "seconds": round(time.time() - t0, 1),
                                "cites": c.get("cites", [])})
            set_model(original)
            CTX.tracer.log(agent="CompareMode", model="multi",
                           prompt={"system": "compare", "user": msg},
                           output={"answer": f"compared {len(results)} tiers"},
                           extra={"modes": [r["mode"] for r in results]})
            self._json({"results": results})
        elif self.path == "/api/creative-chat":
            msg = data.get("message", "").strip()
            low = msg.lower()
            doc = creation_doc()
            if any(low.startswith(w) for w in ("survey me", "new project", "build me", "i want to build", "i want to create", "create a new")):
                self.path = "/api/survey-questions"  # fallthrough not possible; call logic inline below
                data["idea"] = msg
                return self._survey_questions(data)
            edit_words = ("edit", "change", "make ", "rewrite", "add ", "remove", "retitle", "rename", "expand", "shorten", "darker", "lighter")
            if any(w in low for w in edit_words) and doc.exists():
                if CTX.model.mode == "offline":
                    self._json({"type": "chat", "answer": "(offline tier) Document editing needs a model — start Ollama or connect Foundry. I can still answer questions about the project.", "cites": []})
                    return
                ad = art_direction()
                assets_list = ", ".join(Path(a.split("p=")[1]).name for a in assets()) or "none"
                raw = CTX.model.complete(
                    "You are the project's creative editor. Apply the user's instruction to "
                    "the creation document. Stay true to THIS project's domain, tone and "
                    "vocabulary — do not import fantasy/RPG tropes, mythic flavor, or other "
                    "projects' content unless this project is itself a game or campaign. "
                    "Original content only, PG-13. Return ONLY the complete updated "
                    "Markdown document, no commentary.",
                    f"PROJECT: tone={ad['tone']}; about: {ad['goal']}\n"
                    f"EXISTING ASSETS: {assets_list}\n\nINSTRUCTION: {msg}\n\n"
                    f"DOCUMENT:\n{read(doc)[:9000]}")
                if raw and len(raw.strip()) > 100:
                    prev = doc.parent / (doc.stem + "_prev.md")
                    prev.write_text(read(doc), encoding="utf-8")
                    doc.write_text(raw.strip(), encoding="utf-8")
                    with open(proj() / "ITERATION_LOG.md", "a", encoding="utf-8") as fh:
                        fh.write(f"\n## {time.strftime('%Y-%m-%d %H:%M')} — creative chat edit\n"
                                 f"Instruction: {msg[:140]} (previous saved to {prev.name})\n")
                    CTX.tracer.log(agent="CreativeChat", model=CTX.model.mode,
                                   prompt={"system": "doc-edit", "user": msg},
                                   output={"answer": "document updated"}, extra={"project": ACTIVE})
                    self._json({"type": "edited",
                                "answer": f"✓ Document updated (previous version kept as {prev.name}, logged to ITERATION_LOG). "
                                          + raw.strip()[:300] + "…"})
                else:
                    self._json({"type": "chat", "answer": "The edit didn't produce a usable document — try rewording.", "cites": []})
                return
            # default: grounded chat that LOOKS AT the active project's files directly
            fc = (f"PROJECT_STATE: {read(proj() / 'PROJECT_STATE.md')[:500]}\n"
                  f"VISION: {(read(proj() / 'PRODUCT_VISION.md') or read(proj() / 'agile/PRODUCT_VISION.md'))[:500]}\n"
                  f"CREATION DOC: {read(doc)[:700]}\n"
                  f"ASSETS: {', '.join(Path(a.split('p=')[1]).name for a in assets()) or 'none'}")
            c = chat(msg, file_context=fc)
            self._json({"type": "chat", **c})
        elif self.path == "/api/survey-questions":
            return self._survey_questions(data)
        elif self.path == "/api/campaign":
            # Domain-neutral project intake: any idea -> governed KISS project +
            # creation document + a small asset kit GROUNDED in project references.
            import intake_studio as ist
            idea = data.get("idea", "").strip()
            qa = data.get("qa", [])
            answers = [str(x.get("a", "")).strip() for x in qa] + [""] * 5
            if not idea:  # raw survey post: synthesize an idea from the answers
                idea = " ".join(a for a in answers if a) or answers[0]
            tone = ist.detect_tone(idea + " " + " ".join(answers))
            a = {"title_seed": (answers[0] or " ".join(idea.split()[:3]) or "new project").lower(),
                 "tone": tone,
                 "audience": answers[4] or "the intended audience",
                 "must_have": answers[2] or idea[:60],
                 "off_limits": answers[3] or "nothing specified yet"}
            out = output_project_dir(a["title_seed"])
            title = ist.scaffold_project(a, out)

            # --- REFERENCE GROUNDING (search before generating) -----------------
            # 1) the project's own intake signal; 2) related approved knowledge.
            qa_lines = "\n".join(f"Q: {x.get('q','')}\nA: {x.get('a','')}" for x in qa if x.get("a"))
            kb_hits = [h for h in CTX.foundry_iq.retrieve(idea, top_k=20)
                       if not fantasy_hit(h)][:3]
            kb_refs = "\n".join(f"[{h['citation']}] {h['snippet'][:200]}" for h in kb_hits)
            references = (f"INTAKE ANSWERS:\n{qa_lines or '- (none)'}\n\n"
                          f"MUST-HAVE (Tier 1): {a['must_have']}\n"
                          f"AUDIENCE: {a['audience']}\nTONE: {a['tone']}\n\n"
                          f"RELATED KISS KNOWLEDGE (for structure/method, not content):\n{kb_refs or '- (none)'}")
            CTX.tracer.log(agent="IntakeGrounding", model=CTX.model.mode,
                           prompt={"system": "reference-search", "user": idea},
                           grounding=[h["citation"] for h in kb_hits],
                           output={"answer": f"grounded asset+doc generation in {len(kb_hits)} reference(s)"},
                           extra={"project": a["title_seed"]})

            # --- creation document, grounded in references ----------------------
            prose = None
            if CTX.model.mode != "offline":
                prose = ist.llm_creation(CTX.model, idea, a, title, references=references)
            if not prose:
                # offline doc cites reference SOURCES (labels) — never pastes other
                # content's body, so nothing from another project can bleed in.
                kb_cites = "; ".join(h["citation"] for h in kb_hits)
                prose = ist.template_creation(a, title, idea=idea, references=kb_cites)
            (out / "CREATION.md").write_text(prose, encoding="utf-8")

            # --- asset kit: plan from what THIS project needs, grounded ---------
            from asset_governor import AssetGovernor as _AG
            gov = _AG(out)
            pal = ist.palette_for(a["tone"])
            (out / "assets").mkdir(exist_ok=True)
            doc_heads = ", ".join(re.findall(r"^#{2,3} (.+)$", prose, re.M)[:6])
            asset_refs = (f"IDEA: {idea[:160]}\nMUST-HAVE: {a['must_have']}\n"
                          f"AUDIENCE: {a['audience']}\nDOCUMENT SECTIONS: {doc_heads or 'n/a'}")
            reqs = None
            if CTX.model.mode != "offline":
                rawp = CTX.model.complete(
                    "You plan a small visual asset kit for a project. Using the project "
                    "references, return EXACTLY a JSON array of 4-5 assets THIS project "
                    "actually needs. Each item: "
                    '{"type": one of "cover"|"logo"|"palette"|"banner"|"mockup"|"diagram"|"card", '
                    '"label": short specific label}. Choose types that fit the domain '
                    "(brand -> logo, palette, banner; app -> mockup, logo; course/event -> "
                    "cover, card, diagram). JSON only.",
                    "PROJECT REFERENCES:\n" + asset_refs)
                try:
                    s = rawp[rawp.index("["):rawp.rindex("]") + 1]
                    plan = [p for p in json.loads(s)
                            if isinstance(p, dict) and p.get("type") in ist.ASSET_KINDS][:5]
                    if plan:
                        reqs = [(p["type"], str(p.get("label", title))[:40]) for p in plan]
                except Exception:
                    reqs = None
            if not reqs:  # grounded deterministic kit
                reqs = ist.default_asset_kit(title, a["must_have"])

            log = []
            for kind, prompt in reqs:
                d = gov.check(kind, prompt)
                log.append(f"{d['verdict']} {kind}: {prompt[:40]}")
                if d["verdict"] == "ACCEPT":
                    p = out / "assets" / f"{kind}-{gov.counts.get(kind, 0) + 1}.svg"
                    ist.svg_asset(kind, prompt[:36], pal, p, seed=a["title_seed"])
                    gov.record_generation(kind, p.name, d["estimated_cost_usd"])
                elif d["verdict"] == "BLOCK":
                    gov.park(kind, prompt, d["reasons"])

            PROJECTS = discover_projects()
            PROJECTS.update(load_registry())
            ACTIVE = out.name
            safe_index_project(out)
            self._json({"active": ACTIVE, "title": title, "words": len(prose.split()),
                        "governance": log, "references_used": [h["citation"] for h in kb_hits],
                        "projects": list(PROJECTS)})
        elif self.path == "/api/edit-asset":
            rel, instruction = data.get("path", ""), data.get("instruction", "")
            f = (proj() / rel).resolve()
            if not (f.is_file() and proj().resolve() in f.parents and f.suffix == ".svg"):
                self._json({"error": "asset not found"}, 400)
            elif CTX.model.mode == "offline":
                self._json({"error": "AI editing needs a model tier — start Ollama "
                            "or connect Foundry, then retry."}, 400)
            else:
                from asset_governor import AssetGovernor as _AG
                gov = _AG(proj())
                kind = f.stem.split("-")[0]
                d = gov.check(kind if kind in ("cover", "portrait", "map") else "cover",
                              "AI edit: " + instruction)
                if d["verdict"] == "BLOCK":
                    gov.park(kind, instruction, d["reasons"])
                    self._json({"error": "Governor blocked this edit: " + "; ".join(d["reasons"])}, 400)
                else:
                    svg = f.read_text(encoding="utf-8")
                    ad = art_direction()
                    raw = CTX.model.complete(
                        "You are a precise SVG artist. Apply the user's instruction to the "
                        "SVG while staying true to the PROJECT ART CONTEXT (its tone and "
                        "subject). Keep it valid, same canvas size, original-content-only, "
                        "PG-13. Return ONLY the complete edited <svg>...</svg> markup.",
                        f"PROJECT ART CONTEXT: tone={ad['tone']}; about: {ad['goal']}; "
                        f"voice: {ad['voice'] or 'n/a'}\n\n"
                        f"INSTRUCTION: {instruction}\n\nSVG:\n{svg[:6000]}")
                    raw = (raw or "").strip()
                    if "<svg" not in raw:
                        self._json({"error": "model did not return valid SVG — try rewording"}, 400)
                    else:
                        raw = raw[raw.index("<svg"):]
                        if "</svg>" in raw:
                            raw = raw[:raw.rindex("</svg>") + 6]
                        n = 2
                        while (f.parent / f"{f.stem}-v{n}.svg").exists():
                            n += 1
                        newf = f.parent / f"{f.stem}-v{n}.svg"
                        newf.write_text(raw, encoding="utf-8")
                        gov.record_generation(kind, newf.name, d["estimated_cost_usd"])
                        CTX.tracer.log(agent="AssetEditor", model=CTX.model.mode,
                                       prompt={"system": "svg-edit", "user": instruction},
                                       output={"answer": "edited " + rel + " -> " + newf.name},
                                       extra={"project": ACTIVE})
                        self._json({"ok": True, "new": newf.name})
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
