#!/usr/bin/env python3
"""KISS Campaign Studio — Track 1: Creative Apps.

Answer a short survey (= the KISS intake interview) and the studio:
  1. scaffolds a governed KISS project for your campaign (vision, tiers, risk policy),
  2. generates an original fantasy campaign (three acts, NPCs, encounters),
  3. generates art assets — every one passes the Asset Governor's
     policy check (ACCEPT/WARN/BLOCK + cost-before-spend) first.

Offline by default (deterministic content + SVG art, $0). With Microsoft
Foundry configured, prose and art upgrade to model-generated.

Usage:
  python campaign_studio.py --preset          # non-interactive demo survey
  python campaign_studio.py                   # interactive survey
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "foundry-track2"))

from asset_governor import AssetGovernor

SURVEY = [
    ("title_seed", "One or two words that capture your campaign (e.g. 'ember tides')", "ember tides"),
    ("tone", "Tone? (heroic / grim / whimsical)", "heroic"),
    ("setting", "Setting? (coastal / mountain / underdark / desert)", "coastal"),
    ("party_level", "Party level (1-10)?", "3"),
    ("sessions", "How many sessions (1-6)?", "3"),
    ("must_have", "One thing the campaign MUST have", "a sea dragon"),
    ("off_limits", "One thing that is OFF LIMITS (goes straight to the risk policy)", "no player-character death in act 1"),
]

PALETTES = {"heroic": ("#1c4e80", "#f2b134", "#e8e3d3"),
            "grim": ("#2b2b33", "#7a1f2b", "#9aa0a6"),
            "whimsical": ("#4e7a3a", "#d871a9", "#f5e9c8")}
NAMES = ["Maren", "Toskel", "Brialla", "Odric", "Sephine", "Galt", "Yara", "Pell"]
ROLES = ["tide-priest", "smuggler-captain", "lighthouse warden", "storm-witch",
         "guild broker", "exiled cartographer"]


def survey(preset):
    answers = {}
    for key, q, default in SURVEY:
        if preset:
            answers[key] = default
        else:
            v = input(f"{q} [{default}]: ").strip()
            answers[key] = v or default
    return answers


def scaffold_project(a, out):
    out.mkdir(parents=True, exist_ok=True)
    title = a["title_seed"].title()
    (out / "PROJECT_STATE.md").write_text(
        f"# Project State — Campaign '{title}'\n\n"
        "> Source of truth for: current snapshot of the campaign build.\n\n"
        f"**Sprint goal:** ship a playable {a['sessions']}-session campaign with Tier 1 assets\n"
        f"**Status:** active | **Tone:** {a['tone']} | **Setting:** {a['setting']}\n",
        encoding="utf-8")
    (out / "PRODUCT_VISION.md").write_text(
        f"# Product Vision — '{title}'\n\n"
        "## Scope Split\n\n"
        "### In Scope for Tier 1 (this build)\n"
        f"- Three-act outline for {a['sessions']} sessions\n"
        "- 4 named NPCs with hooks\n- 1 cover art\n- 4 character portraits\n- 1 region map\n- 1 session title-card\n"
        f"- Must-have: {a['must_have']}\n\n"
        "### In Scope for Tier 2 (after first session is played)\n"
        "- Per-encounter art\n- Alternate portrait outfits\n- Animated/video intro\n- Ambient music\n\n"
        "### Out of Scope for Now\n- Full illustrated rulebook\n- Voice-acted scenes\n",
        encoding="utf-8")
    (out / "RISK_POLICY.md").write_text(
        f"# Risk Policy — '{title}'\n\n"
        "> Source of truth for: what the AI may do alone vs. what needs the GM.\n\n"
        f"- OFF LIMITS (player rule): {a['off_limits']}\n"
        "- Asset generation is governed by ../templates/ASSET_POLICY.md (tiers, budget, content rules)\n"
        "- Tier 2/3 requests: capture in DECISIONS.md, don't build\n",
        encoding="utf-8")
    (out / "DECISIONS.md").write_text(
        f"# Decisions — '{title}'\n\n"
        "> Source of truth for: locked decisions and parked requests.\n\n"
        f"- **D-C001** | {time.strftime('%Y-%m-%d')} | Tone locked: {a['tone']}; setting: {a['setting']} "
        "| Why: survey intake | Revisit: never mid-campaign\n",
        encoding="utf-8")
    return title


def generate_campaign(a, title, out):
    rng = random.Random(a["title_seed"])  # seeded => reproducible
    names = rng.sample(NAMES, 4)
    roles = rng.sample(ROLES, 4)
    npcs = list(zip(names, roles))
    acts = [
        ("The Hook", f"The {a['setting']} town of Greyharbor calls for help: tides have turned "
                     f"unnatural, and {npcs[0][0]} the {npcs[0][1]} knows why. The party "
                     f"(level {a['party_level']}) is drawn in by a debt, a rumor, and a storm."),
        ("The Turn", f"The trail leads through {npcs[1][0]}'s smuggling routes to a drowned "
                     f"shrine. The must-have arrives: {a['must_have']} — but it is not the enemy "
                     "the party expects. A faction they trusted is feeding it."),
        ("The Reckoning", f"With {npcs[2][0]} and {npcs[3][0]} forced to pick sides, the party "
                          "chooses: bind the threat, bargain with it, or break the cycle that "
                          "summoned it. Three endings, all canon-safe for your table."),
    ]
    md = [f"# {title} — A {a['tone'].title()} Campaign", "",
          f"> Generated by KISS Campaign Studio (offline deterministic mode, seed: '{a['title_seed']}')."
          f" Original fantasy content; policy: templates/ASSET_POLICY.md.", "",
          f"**Sessions:** {a['sessions']} | **Party level:** {a['party_level']} | "
          f"**Table rule (locked):** {a['off_limits']}", "", "## NPCs", ""]
    md += [f"- **{n}**, {r} — hook: knows one secret about the {a['setting']} tides" for n, r in npcs]
    md += ["", "## The Three Acts", ""]
    md += [f"### Act {i+1}: {t}\n\n{body}\n" for i, (t, body) in enumerate(acts)]
    (out / "CAMPAIGN.md").write_text("\n".join(md), encoding="utf-8")
    return npcs


def svg_asset(kind, label, palette, path):
    bg, accent, light = palette
    shapes = {
        "cover": f'<rect width="100%" height="100%" fill="{bg}"/><circle cx="200" cy="150" r="90" fill="{accent}" opacity="0.85"/><path d="M0 260 Q 100 200 200 260 T 400 260 V300 H0 Z" fill="{light}" opacity="0.6"/>',
        "portrait": f'<rect width="100%" height="100%" fill="{light}"/><circle cx="200" cy="120" r="55" fill="{bg}"/><rect x="120" y="180" width="160" height="90" rx="40" fill="{bg}"/><circle cx="200" cy="120" r="55" fill="none" stroke="{accent}" stroke-width="6"/>',
        "map": f'<rect width="100%" height="100%" fill="{light}"/><path d="M40 220 Q 120 80 220 140 T 380 100" stroke="{bg}" stroke-width="5" fill="none"/><circle cx="220" cy="140" r="8" fill="{accent}"/><circle cx="80" cy="200" r="6" fill="{bg}"/><text x="20" y="285" font-size="13" fill="{bg}">shadowed regions = blockers · horizon = deadline</text>',
        "title-card": f'<rect width="100%" height="100%" fill="{bg}"/><rect x="30" y="120" width="340" height="60" fill="{accent}" opacity="0.9"/>',
    }
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
           f'{shapes.get(kind, shapes["cover"])}'
           f'<text x="50%" y="92%" text-anchor="middle" font-family="Georgia" font-size="16" '
           f'fill="{accent if kind != "title-card" else light}">{label}</text></svg>')
    path.write_text(svg, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", action="store_true", help="non-interactive demo survey")
    args = ap.parse_args()

    a = survey(args.preset)
    out = HERE / "output" / a["title_seed"].replace(" ", "-")
    title = scaffold_project(a, out)
    npcs = generate_campaign(a, title, out)
    print(f"\n📜 Campaign '{title}' written → {out / 'CAMPAIGN.md'}")

    gov = AssetGovernor(out)
    palette = PALETTES.get(a["tone"], PALETTES["heroic"])
    assets_dir = out / "assets"
    assets_dir.mkdir(exist_ok=True)

    requests = ([("cover", f"{title} cover, {a['tone']} {a['setting']} scene")]
                + [("portrait", f"{n} the {r}") for n, r in npcs]
                + [("map", f"Region map of Greyharbor ({a['setting']})"),
                   ("title-card", f"Session 1 — {title}"),
                   ("portrait", f"{npcs[0][0]} alternate outfit"),          # exceeds Tier 1 quota → WARN
                   ("video", "Animated intro flythrough of Greyharbor")])   # parked feature → BLOCK

    print("\n🎨 Asset generation (governed by ASSET_POLICY.md):")
    for kind, prompt in requests:
        d = gov.check(kind, prompt)
        tag = {"ACCEPT": "✅", "WARN": "⚠️ ", "BLOCK": "🚫"}[d["verdict"]]
        print(f"  {tag} {d['verdict']:6} {kind:10} ${d['estimated_cost_usd']:.2f}  {prompt[:48]}"
              + (f"  — {d['reasons'][0]}" if d["reasons"] else ""))
        if d["verdict"] == "ACCEPT":
            p = assets_dir / f"{kind}-{gov.counts.get(kind, 0) + 1}.svg"
            svg_asset(kind, prompt[:34], palette, p)
            gov.record_generation(kind, p.name, d["estimated_cost_usd"])
        elif d["verdict"] == "BLOCK":
            gov.park(kind, prompt, d["reasons"])

    print(f"\n  Session spend: ${gov.spend:.2f} | images: {gov.images} | "
          f"unreviewed assets (verification debt): {gov.unreviewed_count()}")
    print(f"  Audit trail: traces/{gov.trace_path.name} | parked requests: {out / 'DECISIONS.md'}")


if __name__ == "__main__":
    main()
