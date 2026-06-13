"""Foundry IQ — grounded knowledge layer.

Demo-grade implementation of the Foundry IQ pattern: a knowledge base built
from approved sources (synthetic certification docs + the pizza-shop project
files), with retrieval that always returns citations. In the hosted version
this maps 1:1 to a Foundry IQ knowledge base over Azure Blob Storage with
agentic retrieval (see README — Deployment).
"""

import re
from pathlib import Path


def is_excluded_source(path: Path) -> bool:
    for p in (path.parent, *path.parents):
        if p.name == "fantasy-template" or (p / ".fantasy").exists():
            return True
    return False


def source_for(path: Path) -> str:
    """Return a stable citation source with project boundaries preserved."""
    if path.parent.name == "knowledge":
        return path.name
    for p in (path.parent, *path.parents):
        if (p / "PROJECT_STATE.md").exists():
            return f"{p.name}/{path.relative_to(p).as_posix()}"
    return f"{path.parent.name}/{path.name}"


class FoundryIQ:
    def __init__(self, source_dirs):
        self.chunks = []  # {source, heading, text}
        for d in source_dirs:
            d = Path(d)
            if not d.exists():
                continue
            for f in sorted(d.rglob("*.md")):
                self._index_file(f)

    def _index_file(self, path: Path):
        if is_excluded_source(path):
            return
        text = path.read_text(encoding="utf-8", errors="replace")
        source = source_for(path)
        heading = path.name
        buf = []
        for line in text.splitlines():
            if line.startswith("#"):
                self._flush(source, heading, buf)
                heading = line.lstrip("# ").strip() or path.name
                buf = []
            else:
                buf.append(line)
        self._flush(source, heading, buf)

    def _flush(self, source, heading, buf):
        body = "\n".join(buf).strip()
        if body:
            self.chunks.append({"source": source, "heading": heading, "text": body})

    def retrieve(self, query: str, top_k: int = 4):
        """Keyword-overlap retrieval with citations."""
        terms = set(re.findall(r"[a-z0-9\-]+", query.lower()))
        scored = []
        for c in self.chunks:
            hay = (c["heading"] + " " + c["text"]).lower()
            score = sum(hay.count(t) for t in terms if len(t) > 2)
            if score:
                scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        results = []
        for score, c in scored[:top_k]:
            results.append({
                "citation": f"{c['source']} § {c['heading']}",
                "snippet": c["text"][:400],
                "score": score,
            })
        return results
