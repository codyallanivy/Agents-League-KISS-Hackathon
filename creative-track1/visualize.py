#!/usr/bin/env python3
"""Vision Layer — `visualize`: turn any KISS project's docs and logs into a
grounded visual so the builder can SEE what they're building.

  docs → decisions → reasoning → VISUALIZATION → understanding

Reads PROJECT_STATE / PRODUCT_VISION / TODO / DECISIONS from a project folder,
composes a grounded visual prompt (never free-floating "AI art" — every element
maps to project data), routes the request through the Asset Governor, then:
  - with Microsoft Foundry image deployment configured: generates real concept art
  - offline: renders a symbolic SVG vision board (tiers as islands, blockers as
    shadow, deadline as horizon) and saves the grounded prompt for later.

Usage:
  python visualize.py ../demo-project/pizza-shop
  python visualize.py output/ember-tides
"""

import argparse
import io
import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import json
import os
import re
import time
from pathlib import Path

from asset_governor import AssetGovernor

HERE = Path(__file__).resolve().parent


def read(p):
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def extract(project: Path):
    state = read(project / "PROJECT_STATE.md")
    vision = read(project / "PRODUCT_VISION.md") or read(project / "agile" / "PRODUCT_VISION.md")
    todo = read(project / "TODO.md")
    decisions = read(project / "DECISIONS.md")

    goal = (re.search(r"(?:Sprint goal|Goal|\*\*Vision\*\*)[:*\s]+(.+)", state + "\n" + vision) or [None, "(no goal found)"])[1].strip()
    tier1 = re.findall(r"- (?:[✅📋❌] )?(?:\[.?\] )?(.+)", (re.search(r"Tier 1.*?\n(.*?)(?=\n###? |\Z)", vision, re.S) or [None, ""])[1])[:6]
    blocked = re.findall(r"- \[~\] ?(.+)", todo)[:4]
    open_tasks = len(re.findall(r"^- \[ \]", todo, re.M))
    done_tasks = len(re.findall(r"^- \[x\]", todo, re.M))
    parked = re.findall(r"Parked[^|]*\| ?(?:Feature: )?([^|]+)", decisions)[:4]
    name = (re.search(r"# Pro[a-z]+ Vision ?[—-] ?'?([^'\n]+?)'?\s*$", vision, re.M)
            or re.search(r"# .*?[—-] ?(?:Campaign )?'?([^'\n]+?)'?\s*$", state, re.M)
            or [None, project.name])[1].strip()
    return {"name": name, "goal": goal, "tier1": [t.strip() for t in tier1],
            "blocked": blocked, "open": open_tasks, "done": done_tasks, "parked": parked}


def grounded_prompt(d):
    return (
        f"Concept art / vision board for the project \"{d['name']}\".\n"
        f"Central image: the goal — {d['goal']}.\n"
        f"Foreground (in warm light): the Tier 1 scope being built now: {', '.join(d['tier1'][:4]) or 'core features'}.\n"
        f"Shadowed regions at the edges: blockers — {', '.join(d['blocked']) or 'none currently'}.\n"
        f"On distant islands across the water (visible but unreachable yet): parked ideas — {', '.join(d['parked']) or 'none'}.\n"
        f"A road from foreground to horizon marks progress: {d['done']} steps laid, {d['open']} remaining.\n"
        "Style: clean, hopeful, storybook-illustration; no text in the image; no real persons; original content only."
    )


def svg_vision_board(d, path):
    deep, accent, mid, light = "#16324f", "#e9a13b", "#9bc1bc", "#f4ecd8"
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;")[:46]
    tier_items = "".join(
        f'<text x="36" y="{170 + i * 19}" font-size="12.5" font-family="Georgia" fill="{light}">◆ {esc(t)}</text>'
        for i, t in enumerate(d["tier1"][:5]))
    shadows = "".join(
        f'<g opacity="0.85"><ellipse cx="{470 + (i % 2) * 60}" cy="{120 + i * 52}" rx="58" ry="20" fill="#000" opacity="0.35"/>'
        f'<text x="{470 + (i % 2) * 60}" y="{124 + i * 52}" font-size="11" font-family="Georgia" fill="{light}" text-anchor="middle" opacity="0.9">{esc(b)}</text></g>'
        for i, b in enumerate(d["blocked"][:3])) or ""
    islands = "".join(
        f'<g><path d="M{120 + i * 130} 96 q22 -16 46 0 q-6 12 -23 12 q-17 0 -23 -12 Z" fill="{deep}" opacity="0.75"/>'
        f'<text x="{143 + i * 130}" y="88" font-size="10.5" font-family="Georgia" font-style="italic" fill="{mid}" text-anchor="middle">{esc(p)}</text></g>'
        for i, p in enumerate(d["parked"][:3]))
    total = max(1, d["open"] + d["done"])
    pct = d["done"] / total
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{deep}"/><stop offset="1" stop-color="{mid}"/></linearGradient>
<radialGradient id="sun" cx="0.5" cy="0.4" r="0.6"><stop offset="0" stop-color="{accent}" stop-opacity="0.9"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient></defs>
<rect width="640" height="400" fill="url(#sky)"/>
<ellipse cx="320" cy="120" rx="200" ry="80" fill="url(#sun)"/>
<text x="320" y="46" font-size="22" font-family="Georgia" letter-spacing="2" fill="{light}" text-anchor="middle">{esc(d['name'])} — Vision Board</text>
<text x="320" y="70" font-size="13" font-family="Georgia" font-style="italic" fill="{mid}" text-anchor="middle">{esc(d['goal'])}</text>
<line x1="0" y1="110" x2="640" y2="110" stroke="{light}" stroke-width="1" opacity="0.5"/>
<text x="608" y="104" font-size="10" font-family="Georgia" fill="{light}" opacity="0.8" text-anchor="end">horizon = deadline</text>
{islands}
<path d="M0 270 Q120 232 240 256 T480 250 T640 246 V400 H0 Z" fill="{deep}"/>
<rect x="24" y="142" width="250" height="{36 + 19 * max(1, len(d['tier1'][:5]))}" rx="8" fill="#000" opacity="0.25"/>
<text x="36" y="150" font-size="12" font-family="Georgia" fill="{accent}" letter-spacing="2">BUILDING NOW (TIER 1)</text>
{tier_items}
{shadows}
<path d="M60 386 Q200 350 320 330 T610 296" stroke="{light}" stroke-width="3" stroke-dasharray="7 6" fill="none" opacity="0.9"/>
<circle cx="{60 + 550 * pct}" cy="{386 - 90 * pct}" r="7" fill="{accent}"/>
<text x="36" y="376" font-size="11.5" font-family="Georgia" fill="{light}">progress: {d['done']} done · {d['open']} open</text>
<text x="320" y="394" font-size="10" font-family="Georgia" font-style="italic" fill="{mid}" text-anchor="middle">every element maps to project data — shadows = blockers · islands = parked ideas · road = TODO.md</text>
</svg>'''
    path.write_text(svg, encoding="utf-8")


def try_foundry_image(prompt, out_path):
    """Generate real concept art via Microsoft Foundry image deployment, if configured."""
    endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "").strip()
    deployment = os.getenv("AZURE_AI_IMAGE_DEPLOYMENT", "").strip()
    if not (endpoint and deployment):
        return None
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
        import base64
        client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
        openai = client.get_openai_client(api_version="2024-10-21")
        r = openai.images.generate(model=deployment, prompt=prompt, size="1024x1024",
                                   response_format="b64_json")
        out_path.write_bytes(base64.b64decode(r.data[0].b64_json))
        return out_path
    except Exception as exc:
        print(f"[warn] Foundry image generation unavailable ({exc}) — SVG vision board instead.")
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", help="path to a KISS project folder")
    args = ap.parse_args()
    project = Path(args.project).resolve()

    d = extract(project)
    prompt = grounded_prompt(d)
    print(f"🔭 Vision Layer — '{d['name']}'\n\nGrounded visual prompt (every line maps to project data):\n{prompt}\n")

    gov = AssetGovernor(project)
    mode = "foundry-image" if os.getenv("AZURE_AI_IMAGE_DEPLOYMENT") else "offline-svg"
    decision = gov.check("cover", "project vision board: " + d["name"], mode=mode)
    tag = {"ACCEPT": "✅", "WARN": "⚠️", "BLOCK": "🚫"}[decision["verdict"]]
    print(f"{tag} Asset Governor: {decision['verdict']} (est. ${decision['estimated_cost_usd']:.2f})"
          + (f" — {decision['reasons'][0]}" if decision["reasons"] else ""))
    if decision["verdict"] == "BLOCK":
        gov.park("vision-board", prompt, decision["reasons"])
        return

    vis_dir = project / "vision"
    vis_dir.mkdir(exist_ok=True)
    (vis_dir / "vision_prompt.txt").write_text(prompt, encoding="utf-8")
    png = try_foundry_image(prompt, vis_dir / "vision_board.png")
    if png:
        gov.record_generation("vision-board", png.name, decision["estimated_cost_usd"])
        print(f"🖼  Concept art generated → {png}")
    else:
        svg = vis_dir / "vision_board.svg"
        svg_vision_board(d, svg)
        gov.record_generation("vision-board", svg.name, 0.0)
        print(f"🗺  Vision board rendered → {svg}\n    (set AZURE_AI_IMAGE_DEPLOYMENT for model-generated concept art)")


if __name__ == "__main__":
    main()
