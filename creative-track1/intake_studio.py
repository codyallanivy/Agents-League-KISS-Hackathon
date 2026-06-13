#!/usr/bin/env python3
"""KISS Intake Studio — Track 1: the general project intake engine.

This is the survey/intake mechanism at the heart of the Creative Studio. It takes
ANY project idea (a brand, an app, a course, an event, a campaign, a product...),
runs an adaptive intake survey to expand and clarify it, scaffolds a governed KISS
project, and produces a primary creation document plus a small, governed asset kit.

It is deliberately DOMAIN-NEUTRAL. There are no fantasy/RPG defaults, names, or
art here. The optional tabletop "Fantasy Campaign" example lives, fully isolated,
in `fantasy-template/` and never influences this module.

Content quality ladder (research: "Community Open Model Path"):
  1. Microsoft Foundry (AZURE_AI_PROJECT_ENDPOINT set)  — cloud model
  2. Ollama local open-weight model (if running)        — free, private
  3. Deterministic seeded templates                     — always works

Usage:
  python intake_studio.py --preset   # non-interactive demo (a sample brand)
  python intake_studio.py            # interactive intake survey
"""

import argparse
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "foundry-track2"))

from asset_governor import AssetGovernor
from agents.base_agent import ModelClient  # reuse the 3-tier model ladder

# ---- the adaptive intake survey (general-purpose) -----------------------------
# Used when no free-text idea is supplied. When an idea IS supplied, the Command
# Center generates tailored questions from it; these are the durable fallbacks.
INTAKE = [
    ("title_seed", "What should we call it? (a name or a few seed words)", "northwind brew"),
    ("audience", "Who is it for? (the primary audience)", "neighborhood coffee drinkers"),
    ("tone", "Look and feel? (clean / warm / bold / calm)", "warm"),
    ("must_have", "The ONE thing v1 must have?", "a logo and a tagline"),
    ("off_limits", "What is explicitly OUT of scope for now?", "a full e-commerce store"),
]

# Neutral, modern palettes keyed by tone -> (deep, accent, mid, light).
PALETTES = {
    "clean": ("#1f2937", "#3b82f6", "#94a3b8", "#f1f5f9"),
    "warm":  ("#3b2415", "#e08a3c", "#caa67a", "#f6ece1"),
    "bold":  ("#12101a", "#f43f5e", "#6366f1", "#e7e7ef"),
    "calm":  ("#16302b", "#2dd4bf", "#7da39b", "#eef6f3"),
    "grim":  ("#1d1d26", "#7a1f2b", "#4a4e69", "#c9c4b4"),
}
# Legacy tone aliases (so older callers never crash) map onto neutral palettes.
PALETTE_ALIASES = {"heroic": "clean", "whimsical": "warm", "default": "clean"}

# Asset kinds this module knows how to draw, with the kind of project they suit.
ASSET_KINDS = ("cover", "logo", "palette", "banner", "mockup", "diagram", "card")


def palette_for(tone):
    tone = (tone or "clean").lower()
    return PALETTES.get(tone) or PALETTES.get(PALETTE_ALIASES.get(tone, "clean"))


def detect_tone(text):
    t = (text or "").lower()
    if any(w in t for w in ("grim", "dark", "noir", "serious", "premium", "luxury", "somber")):
        return "bold"
    if any(w in t for w in ("calm", "minimal", "clean", "clinical", "modern", "tech")):
        return "calm" if "calm" in t else "clean"
    if any(w in t for w in ("warm", "cozy", "friendly", "homey", "playful", "fun")):
        return "warm"
    return "clean"


def survey(preset):
    answers = {}
    for key, q, default in INTAKE:
        answers[key] = default if preset else (input(f"{q} [{default}]: ").strip() or default)
    return answers


def scaffold_project(a, out):
    """Create the governed KISS memory files for a general project."""
    out.mkdir(parents=True, exist_ok=True)
    title = a["title_seed"].title()
    tone = a.get("tone", "clean")
    audience = a.get("audience", "the intended audience")
    (out / "PROJECT_STATE.md").write_text(
        f"# Project State — {title}\n\n"
        "> Source of truth for: the CURRENT snapshot of this project.\n\n"
        f"**Sprint goal:** ship the smallest v1 of {title} that delivers its must-have\n"
        f"**Status:** active | **Tone:** {tone} | **Audience:** {audience}\n", encoding="utf-8")
    (out / "PRODUCT_VISION.md").write_text(
        f"# Product Vision — {title}\n\n## Scope Split\n\n"
        "### In Scope for Tier 1 (build now)\n"
        f"- {a.get('must_have', 'the core must-have')}\n"
        "- The primary creation document (CREATION.md)\n"
        "- A small starter asset kit (cover + supporting pieces)\n\n"
        "### In Scope for Tier 2 (after Tier 1 ships)\n"
        "- Expanded asset set and variations\n- Polish and secondary flows\n\n"
        "### Out of Scope for Now\n"
        f"- {a.get('off_limits', 'anything beyond the must-have')}\n", encoding="utf-8")
    (out / "RISK_POLICY.md").write_text(
        f"# Risk Policy — {title}\n\n"
        "> Source of truth for: what an AI agent may do alone vs. what needs the owner.\n\n"
        f"- OFF LIMITS for now: {a.get('off_limits', 'nothing specified yet')}\n"
        "- Asset generation governed by ../templates/ASSET_POLICY.md\n"
        "- Tier 2/3 requests: capture in DECISIONS.md, don't build\n", encoding="utf-8")
    (out / "DECISIONS.md").write_text(
        f"# Decisions — {title}\n\n"
        "> Source of truth for: locked decisions and parked requests.\n\n"
        f"- **D-001** | {time.strftime('%Y-%m-%d')} | Tone locked: {tone}; audience: {audience} "
        "| Why: intake survey | Revisit: when the audience changes\n", encoding="utf-8")
    # Seed a real backlog so a freshly-generated project is immediately
    # workflow-complete in Project Ops (board / next-best-work / health / popsicle).
    (out / "TODO.md").write_text(
        f"# To Do — {title}\n\n"
        "> Source of truth for: the real backlog. [ ] open · [x] done · [~] blocked.\n\n"
        "## Now\n"
        f"- [ ] {a.get('must_have', 'Build the core must-have')} | medium\n"
        "- [ ] Fill PRODUCT_VISION.md tiers (confirm what's v1 vs parked) | light\n"
        "- [ ] Verify the first version with a real person before adding more | medium\n\n"
        "## Later\n"
        "- [ ] Expand the asset set after Tier 1 ships | —\n", encoding="utf-8")
    return title


def llm_creation(model, idea, a, title, references=""):
    """Tier 1/2: a real model writes the primary creation document, grounded in
    the intake answers and any retrieved project references."""
    system = ("You are a creative director and project planner. Produce the primary "
              "creation document for THIS project — whatever fits the idea (brand kit, "
              "product concept, app spec, course outline, event plan, campaign...). "
              "Write in the project's own domain and vocabulary. Original content only, "
              "PG-13. Clean Markdown, 600-1000 words, ending with '## Next Steps' "
              "(3 concrete bullets). Do not invent details that contradict the references.")
    ref_block = f"\n\nPROJECT REFERENCES (ground your document in these):\n{references}" if references else ""
    user = (f"IDEA: {idea or title}\nAUDIENCE: {a.get('audience','')}\n"
            f"TONE: {a.get('tone','')}\nMUST-HAVE (Tier 1): {a.get('must_have','')}\n"
            f"OUT OF SCOPE: {a.get('off_limits','')}{ref_block}")
    return model.complete(system, user)


def template_creation(a, title, idea="", references=""):
    """Tier 3: deterministic, neutral creation document seeded by the intake."""
    must = a.get("must_have", "the core must-have")
    return (
        f"# {title}\n\n"
        f"> Generated offline (deterministic intake seed). Original content; for a "
        f"full draft, run with Ollama or Microsoft Foundry configured.\n\n"
        f"**Audience:** {a.get('audience','')} · **Tone:** {a.get('tone','')} · "
        f"**Out of scope (locked):** {a.get('off_limits','')}\n\n"
        f"## The Idea\n\n{idea or title}\n\n"
        f"## What v1 Must Deliver\n\n- {must}\n\n"
        f"## Three-Phase Plan\n\n"
        f"1. **Shape it** — turn the must-have into one testable Tier 1 outcome.\n"
        f"2. **Build the smallest version** — only what Tier 1 needs; park everything "
        f"else in DECISIONS.md.\n"
        f"3. **Verify with a real person** — before adding anything new.\n\n"
        + (f"## Grounded References\n\n{references}\n\n" if references else "")
        + f"## Next Steps\n\n- Fill the PRODUCT_VISION.md tiers\n"
        f"- Set the sprint goal in PROJECT_STATE.md\n- Generate the vision board\n")


# ---- neutral, brand/product-style SVG assets (offline tier) -------------------
def svg_asset(kind, label, pal, path, seed="", fantasy=False):
    """Clean, modern, art-directed SVG assets. No fantasy motifs — these read as
    brand/product collateral and suit any project domain. `fantasy` is accepted
    for signature compatibility and intentionally ignored."""
    deep, accent, mid, light = pal
    rng = random.Random(str(seed) + kind + label)

    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;")[:40]

    defs = (
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{deep}"/><stop offset="1" stop-color="{mid}"/></linearGradient>'
        f'<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="{mid}"/></linearGradient></defs>')

    if kind == "logo":
        initials = "".join(w[0] for w in str(label).split()[:2]).upper() or "K"
        body = (f'<rect width="400" height="300" fill="{light}"/>'
                f'<rect x="132" y="82" width="136" height="136" rx="28" fill="url(#bg)"/>'
                f'<circle cx="200" cy="150" r="78" fill="none" stroke="{accent}" stroke-width="4" opacity="0.9"/>'
                f'<text x="200" y="168" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" '
                f'font-size="58" font-weight="700" fill="{light}">{esc(initials)}</text>')
        text_fill, ty = deep, 252
    elif kind == "palette":
        chips = ""
        for i, c in enumerate((deep, accent, mid, light)):
            x = 36 + i * 84
            chips += (f'<rect x="{x}" y="78" width="72" height="120" rx="10" fill="{c}" '
                      f'stroke="{deep}" stroke-opacity="0.15"/>'
                      f'<rect x="{x}" y="170" width="72" height="28" rx="0" fill="#000" opacity="0.12"/>')
        body = f'<rect width="400" height="300" fill="{light}"/>{chips}'
        text_fill, ty = deep, 240
    elif kind == "banner":
        body = (f'<rect width="400" height="300" fill="url(#bg)"/>'
                f'<rect x="0" y="196" width="400" height="6" fill="url(#acc)"/>'
                f'<circle cx="58" cy="150" r="34" fill="{accent}" opacity="0.9"/>'
                f'<rect x="110" y="132" width="210" height="12" rx="6" fill="{light}" opacity="0.85"/>'
                f'<rect x="110" y="156" width="150" height="9" rx="4" fill="{light}" opacity="0.55"/>')
        text_fill, ty = light, 250
    elif kind == "mockup":
        lines = "".join(f'<rect x="150" y="{120 + i*22}" width="{rng.choice([140,170,120])}" '
                        f'height="10" rx="5" fill="{mid}" opacity="0.7"/>' for i in range(4))
        body = (f'<rect width="400" height="300" fill="{light}"/>'
                f'<rect x="118" y="60" width="164" height="200" rx="16" fill="#fff" '
                f'stroke="{deep}" stroke-opacity="0.18"/>'
                f'<rect x="118" y="60" width="164" height="34" rx="16" fill="url(#bg)"/>'
                f'<rect x="118" y="78" width="164" height="16" fill="url(#bg)"/>'
                f'<circle cx="150" cy="77" r="6" fill="{accent}"/>{lines}'
                f'<rect x="150" y="216" width="100" height="26" rx="13" fill="{accent}"/>')
        text_fill, ty = deep, 280
    elif kind == "diagram":
        nodes = [("Tier 1", 70), ("Core", 200), ("Later", 330)]
        g = (f'<line x1="70" y1="150" x2="330" y2="150" stroke="{mid}" stroke-width="3" '
             f'stroke-dasharray="6 5"/>')
        for i, (lbl, x) in enumerate(nodes):
            fill = accent if i == 0 else (mid if i == 1 else deep)
            g += (f'<circle cx="{x}" cy="150" r="30" fill="{fill}"/>'
                  f'<text x="{x}" y="206" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" '
                  f'font-size="13" fill="{deep}">{esc(lbl)}</text>')
        body = f'<rect width="400" height="300" fill="{light}"/>{g}'
        text_fill, ty = deep, 70
    elif kind == "card":
        body = (f'<rect width="400" height="300" fill="{light}"/>'
                f'<rect x="40" y="50" width="320" height="200" rx="16" fill="#fff" '
                f'stroke="{deep}" stroke-opacity="0.15"/>'
                f'<rect x="40" y="50" width="320" height="64" rx="16" fill="url(#bg)"/>'
                f'<rect x="40" y="98" width="320" height="16" fill="url(#bg)"/>'
                f'<rect x="64" y="148" width="200" height="10" rx="5" fill="{mid}" opacity="0.7"/>'
                f'<rect x="64" y="172" width="260" height="10" rx="5" fill="{mid}" opacity="0.5"/>'
                f'<rect x="64" y="206" width="120" height="26" rx="13" fill="{accent}"/>')
        text_fill, ty = light, 92
    else:  # "cover" (default) — clean branded cover card
        shapes = "".join(
            f'<circle cx="{rng.randint(40,360)}" cy="{rng.randint(30,120)}" '
            f'r="{rng.choice([6,10,14])}" fill="{light}" opacity="{rng.choice([0.10,0.16,0.22])}"/>'
            for _ in range(7))
        body = (f'<rect width="400" height="300" fill="url(#bg)"/>{shapes}'
                f'<rect x="0" y="150" width="400" height="6" fill="url(#acc)"/>'
                f'<circle cx="320" cy="78" r="40" fill="{accent}" opacity="0.85"/>'
                f'<rect x="40" y="120" width="120" height="10" rx="5" fill="{light}" opacity="0.8"/>')
        text_fill, ty = light, 250

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">{defs}{body}'
           f'<text x="50%" y="{ty}" text-anchor="middle" '
           f'font-family="Helvetica,Arial,sans-serif" font-size="16" letter-spacing="0.5" '
           f'fill="{text_fill}">{esc(label)}</text></svg>')
    path.write_text(svg, encoding="utf-8")


# ---- default asset kit per project (used when no model plan is available) ------
def default_asset_kit(title, must_have=""):
    kit = [("cover", title), ("logo", title), ("palette", "Brand palette"),
           ("diagram", "Three-phase plan")]
    if must_have:
        kit.append(("card", must_have[:36]))
    return kit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", action="store_true")
    args = ap.parse_args()

    a = survey(args.preset)
    a["tone"] = detect_tone(a.get("tone", "") + " " + a.get("title_seed", ""))
    out = HERE / "output" / a["title_seed"].replace(" ", "-")
    title = scaffold_project(a, out)

    model = ModelClient()
    print(f"\n📝  Writing creation document (content tier: {model.mode}) …")
    prose = None
    if model.mode != "offline":
        prose = llm_creation(model, a["title_seed"], a, title)
    if not prose:
        prose = template_creation(a, title, idea=a["title_seed"])
    (out / "CREATION.md").write_text(prose, encoding="utf-8")
    print(f"📄 Creation doc '{title}' → {out / 'CREATION.md'} ({len(prose.split())} words)")

    gov = AssetGovernor(out)
    pal = palette_for(a["tone"])
    assets = out / "assets"
    assets.mkdir(exist_ok=True)
    print("\n🎨 Asset generation (governed by ASSET_POLICY.md):")
    for kind, prompt in default_asset_kit(title, a.get("must_have", "")):
        d = gov.check(kind, prompt)
        tag = {"ACCEPT": "✅", "WARN": "⚠️ ", "BLOCK": "🚫"}[d["verdict"]]
        print(f"  {tag} {d['verdict']:6} {kind:9} ${d['estimated_cost_usd']:.2f}  {prompt[:42]}"
              + (f"  — {d['reasons'][0]}" if d["reasons"] else ""))
        if d["verdict"] == "ACCEPT":
            p = assets / f"{kind}-{gov.counts.get(kind, 0) + 1}.svg"
            svg_asset(kind, prompt[:36], pal, p, seed=a["title_seed"])
            gov.record_generation(kind, p.name, d["estimated_cost_usd"])
        elif d["verdict"] == "BLOCK":
            gov.park(kind, prompt, d["reasons"])

    print(f"\n  Session spend: ${gov.spend:.2f} | images: {gov.images} | "
          f"unreviewed (verification debt): {gov.unreviewed_count()}")
    print(f"  Audit: traces/{gov.trace_path.name} | parked: {out / 'DECISIONS.md'}")


if __name__ == "__main__":
    main()
