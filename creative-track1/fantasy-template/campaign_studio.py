#!/usr/bin/env python3
"""Fantasy Campaign template — an OPTIONAL, self-contained example project.

This is a *side template* that shows the KISS system is general enough to even
author a tabletop-RPG campaign. It is deliberately ISOLATED: it writes only into
this `fantasy-template/` folder, it is NOT discovered as a project by the Command
Center, and its output is NEVER indexed into the shared knowledge base. Nothing
here influences how any other project is planned, surveyed, or generated.

Launch it only on purpose: `start.bat` -> option 3, or run this file directly.

Content quality ladder (research: "Community Open Model Path"):
  1. Microsoft Foundry (AZURE_AI_PROJECT_ENDPOINT set)  — cloud model
  2. Ollama local open-weight model (if running)        — free, private
  3. Deterministic seeded templates                     — always works

Usage:
  python campaign_studio.py --preset   # non-interactive demo
  python campaign_studio.py            # interactive survey
"""

import argparse
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent          # creative-track1/fantasy-template
CT1 = HERE.parent                                # creative-track1 (asset_governor lives here)
ROOT = CT1.parent                                # repo root
sys.path.insert(0, str(ROOT / "foundry-track2"))
sys.path.insert(0, str(CT1))

from asset_governor import AssetGovernor
from agents.base_agent import ModelClient  # reuse the 3-tier model ladder

SURVEY = [
    ("title_seed", "One or two words that capture your campaign (e.g. 'ember tides')", "ember tides"),
    ("tone", "Tone? (heroic / grim / whimsical)", "heroic"),
    ("setting", "Setting? (coastal / mountain / underdark / desert)", "coastal"),
    ("party_level", "Party level (1-10)?", "3"),
    ("sessions", "How many sessions (1-6)?", "3"),
    ("must_have", "One thing the campaign MUST have", "a sea dragon"),
    ("off_limits", "One thing that is OFF LIMITS (goes straight to the risk policy)", "no player-character death in act 1"),
]

PALETTES = {"heroic": ("#16324f", "#e9a13b", "#9bc1bc", "#f4ecd8"),
            "grim": ("#1d1d26", "#7a1f2b", "#4a4e69", "#c9c4b4"),
            "whimsical": ("#3a5a40", "#d871a9", "#83c5be", "#fff3d6")}
NAMES = ["Maren", "Toskel", "Brialla", "Odric", "Sephine", "Galt", "Yara", "Pell"]
ROLES = ["tide-priest", "smuggler-captain", "lighthouse warden", "storm-witch",
         "guild broker", "exiled cartographer", "salvage diver", "harbor magistrate"]
MOTIVES = ["owes a life-debt to the party's patron", "is secretly feeding the threat",
           "wants the old order restored", "is protecting a sibling's secret",
           "collects forbidden charts", "believes the tides speak"]
LOCATIONS = ["the drowned shrine of the First Light", "a smugglers' cove under the cliffs",
             "the rusted lighthouse on Gull Point", "the night-market on the pier",
             "a wreck haunted by salt-ghosts", "the magistrate's flooded archive"]
COMPLICATIONS = ["the tide turns two hours early", "a rival crew arrives first",
                 "the relic is a fake — the real one was traded away",
                 "an NPC the party trusts lies to protect someone",
                 "a storm forces an impossible choice between two goals"]


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
    # Hard isolation marker: any project scanner / knowledge indexer skips dirs
    # containing this file, so a fantasy campaign can never leak into another
    # project's planning or grounded output.
    (out / ".fantasy").write_text("isolated fantasy template output — do not index\n", encoding="utf-8")
    title = a["title_seed"].title()
    (out / "PROJECT_STATE.md").write_text(
        f"# Project State — Campaign '{title}'\n\n"
        "> Source of truth for: current snapshot of the campaign build.\n\n"
        f"**Sprint goal:** ship a playable {a['sessions']}-session campaign with Tier 1 assets\n"
        f"**Status:** active | **Tone:** {a['tone']} | **Setting:** {a['setting']}\n", encoding="utf-8")
    (out / "PRODUCT_VISION.md").write_text(
        f"# Product Vision — '{title}'\n\n## Scope Split\n\n"
        "### In Scope for Tier 1 (this build)\n"
        f"- Three-act outline for {a['sessions']} sessions\n"
        "- 4 named NPCs with hooks\n- 1 cover art\n- 4 character portraits\n- 1 region map\n- 1 session title-card\n"
        f"- Must-have: {a['must_have']}\n\n"
        "### In Scope for Tier 2 (after first session is played)\n"
        "- Per-encounter art\n- Alternate portrait outfits\n- Animated/video intro\n- Ambient music\n\n"
        "### Out of Scope for Now\n- Full illustrated rulebook\n- Voice-acted scenes\n", encoding="utf-8")
    (out / "RISK_POLICY.md").write_text(
        f"# Risk Policy — '{title}'\n\n"
        "> Source of truth for: what the AI may do alone vs. what needs the GM.\n\n"
        f"- OFF LIMITS (player rule): {a['off_limits']}\n"
        "- Asset generation governed by ../templates/ASSET_POLICY.md\n"
        "- Tier 2/3 requests: capture in DECISIONS.md, don't build\n", encoding="utf-8")
    (out / "DECISIONS.md").write_text(
        f"# Decisions — '{title}'\n\n"
        "> Source of truth for: locked decisions and parked requests.\n\n"
        f"- **D-C001** | {time.strftime('%Y-%m-%d')} | Tone locked: {a['tone']}; setting: {a['setting']} "
        "| Why: survey intake | Revisit: never mid-campaign\n", encoding="utf-8")
    return title


def llm_campaign(model, a, title, npcs):
    """Tier 1/2 of the ladder: real model writes the campaign, grounded in the survey."""
    npc_lines = "\n".join(f"- {n}, {r} — {m}" for n, r, m in npcs)
    system = ("You are a veteran tabletop-RPG campaign designer. Write original fantasy "
              "content only — no franchise IP, no real persons, PG-13. Respect every "
              "constraint given. Output clean Markdown.")
    user = (f"Write a {a['sessions']}-session campaign called '{title}'.\n"
            f"Tone: {a['tone']}. Setting: {a['setting']}. Party level: {a['party_level']}.\n"
            f"MUST include: {a['must_have']}. TABLE RULE (hard constraint): {a['off_limits']}.\n"
            f"Use these NPCs:\n{npc_lines}\n\n"
            "Structure: ## Premise (1 paragraph, evocative); ## NPCs (one rich line each: "
            "appearance, motive, secret); ## Act 1/2/3 — each with an overview paragraph, "
            "a boxed read-aloud intro in italics, three scenes (location, what happens, "
            "a skill/combat hint), and a twist; ## Three Endings (one paragraph each). "
            "800-1200 words.")
    return model.complete(system, user)


def template_campaign(a, title, npcs, rng):
    """Tier 3: deterministic but genuinely rich, seeded by the survey."""
    locs = rng.sample(LOCATIONS, 6)
    comps = rng.sample(COMPLICATIONS, 3)
    md = [f"# {title} — A {a['tone'].title()} Campaign",
          "",
          f"> Generated offline (deterministic seed '{a['title_seed']}'). Original fantasy content; "
          "policy: templates/ASSET_POLICY.md. For richer prose, run with Ollama or Foundry configured.",
          "",
          f"**Sessions:** {a['sessions']} · **Party level:** {a['party_level']} · "
          f"**Table rule (locked):** {a['off_limits']}",
          "", "## Premise", "",
          f"Greyharbor has always lived by the tide-bells, but for nine nights the bells have rung "
          f"backwards. Nets come up empty or come up *wrong*. The harbor folk whisper that the old "
          f"compact with the deep is broken — and that {a['must_have']} has returned to collect. "
          f"Into this {a['tone']} {a['setting']} town comes the party: not chosen ones, just the "
          f"only people foolish enough to ask *why*.",
          "", "## NPCs", ""]
    for n, r, m in npcs:
        md.append(f"- **{n}**, {r} — weather-worn, sharper than they look; {m}. "
                  f"Secret: they were at {locs[0]} the night the bells changed.")
    act_data = [
        ("The Hook", locs[0], locs[1], comps[0],
         f"The party arrives as a funeral barge drifts in with no body aboard — only a tide-bell, "
         f"still ringing. {npcs[0][0]} hires them quietly: find what the sea returned, before the "
         f"magistrate does."),
        ("The Turn", locs[2], locs[3], comps[1],
         f"The trail leads through {npcs[1][0]}'s old routes. Here the must-have surfaces: "
         f"{a['must_have']}, vast and patient — and not the villain. Something *fed* it the town's "
         f"bargain. A faction the party trusted holds the contract."),
        ("The Reckoning", locs[4], locs[5], comps[2],
         f"With {npcs[2][0]} and {npcs[3][0]} forced onto opposite sides, the party holds the "
         f"compact's last unbroken clause. Bind, bargain, or break — Greyharbor will live with "
         f"whichever they choose."),
    ]
    for i, (name, l1, l2, comp, overview) in enumerate(act_data, 1):
        md += ["", f"## Act {i}: {name}", "", overview, "",
               f"> *Read aloud: The {a['setting']} wind drops. Somewhere beneath the boards, "
               f"water moves against the tide. You are being listened to.*", "",
               f"**Scene 1 — {l1}.** Investigation and roleplay. A clue points two directions at "
               f"once; let the players choose and make the unchosen path matter later. "
               f"(Insight/Investigation, moderate DC.)",
               f"**Scene 2 — {l2}.** Set-piece: a skirmish or chase shaped by the terrain — "
               f"rising water, narrow walkways, light that fails at the worst moment. "
               f"(Combat or chase, level {a['party_level']} appropriate.)",
               f"**Scene 3 — Complication.** {comp.capitalize()}. The act's plan survives only "
               f"if the players adapt. (No roll fixes this; decisions do.)",
               "", f"**Twist:** an ally's motive from the NPC list pays off here — "
               f"{npcs[(i - 1) % 4][0]} {npcs[(i - 1) % 4][2]}."]
    md += ["", "## Three Endings", "",
           "**Bind** — the compact is rewritten in the party's names: safety, owed forever.",
           "**Bargain** — the deep takes a tithe and a truth; Greyharbor prospers, changed.",
           "**Break** — the bells fall silent for good. Freedom, and weather with no promises.",
           "", f"*Table rule honored throughout: {a['off_limits']}.*"]
    return "\n".join(md)


def svg_asset(kind, label, pal, path, seed="", fantasy=True):
    """Layered, art-directed SVG compositions (offline tier)."""
    deep, accent, mid, light = pal
    rng = random.Random(seed + kind + label)
    stars = "".join(f'<circle cx="{rng.randint(8, 392)}" cy="{rng.randint(8, 120)}" r="{rng.choice([0.8, 1.2, 1.6])}" fill="{light}" opacity="{rng.choice([0.4, 0.7, 0.9])}"/>' for _ in range(26))
    defs = (f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{deep}"/><stop offset="1" stop-color="{mid}"/></linearGradient>'
            f'<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{mid}"/><stop offset="1" stop-color="{deep}"/></linearGradient>'
            f'<radialGradient id="glow" cx="0.5" cy="0.45" r="0.5">'
            f'<stop offset="0" stop-color="{accent}" stop-opacity="0.95"/>'
            f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient></defs>')
    if kind == "cover":
        body = (f'<rect width="400" height="300" fill="url(#sky)"/>{stars}'
                f'<circle cx="300" cy="78" r="34" fill="{light}" opacity="0.92"/>'
                f'<circle cx="312" cy="70" r="30" fill="url(#sky)"/>'
                f'<ellipse cx="200" cy="150" rx="150" ry="70" fill="url(#glow)"/>'
                f'<path d="M0 190 Q60 150 120 185 T240 180 T400 175 V300 H0 Z" fill="url(#sea)"/>'
                f'<path d="M0 215 Q80 195 160 212 T320 208 T400 210 V300 H0 Z" fill="{deep}" opacity="0.85"/>'
                f'<path d="M150 185 q28 -90 64 -118 q8 38 -6 64 q30 -8 44 -30 q4 50 -38 76 q-34 16 -64 8 Z" fill="{deep}" stroke="{accent}" stroke-width="2.5" opacity="0.95"/>'
                f'<circle cx="206" cy="98" r="3.4" fill="{accent}"/>'
                f'<path d="M40 245 l26 -10 6 -22 8 20 24 4 -20 12 2 24 -18 -14 -22 8 6 -20 Z" fill="{accent}" opacity="0.25"/>')
    elif kind == "portrait":
        body = (f'<rect width="400" height="300" fill="url(#sky)"/>{stars}'
                f'<ellipse cx="200" cy="135" rx="120" ry="105" fill="url(#glow)" opacity="0.8"/>'
                f'<path d="M120 300 q-6 -90 34 -126 q-18 -36 8 -68 q22 -28 48 -22 q30 6 40 36 q10 28 -8 54 q40 34 36 126 Z" fill="{deep}"/>'
                f'<path d="M150 110 q10 -44 50 -40 q36 4 38 44 q2 30 -22 44 q-44 10 -58 -14 q-10 -16 -8 -34 Z" fill="{mid}"/>'
                f'<path d="M148 132 q52 26 102 -2" stroke="{accent}" stroke-width="3" fill="none"/>'
                f'<path d="M118 298 q4 -82 36 -118" stroke="{accent}" stroke-width="2.4" fill="none" opacity="0.85"/>'
                f'<circle cx="246" cy="106" r="4" fill="{accent}"/>')
    elif kind == "map":
        poi_labels = ([(120, 95, "Drowned Shrine"), (236, 150, "Greyharbor"), (96, 208, "Gull Point"), (300, 90, "the Wreck")]
                      if fantasy else
                      [(120, 95, "Phase 1"), (236, 150, "Core"), (96, 208, "Phase 2"), (300, 90, "Later")])
        pois = "".join(f'<g><circle cx="{x}" cy="{y}" r="5.5" fill="{accent}"/><circle cx="{x}" cy="{y}" r="9" fill="none" stroke="{accent}" stroke-width="1" opacity="0.5"/><text x="{x + 13}" y="{y + 4}" font-size="11" font-family="Georgia" fill="{deep}">{t}</text></g>'
                       for x, y, t in poi_labels)
        body = (f'<rect width="400" height="300" fill="{light}"/>'
                f'<rect x="8" y="8" width="384" height="284" fill="none" stroke="{deep}" stroke-width="2" opacity="0.6"/>'
                f'<rect x="13" y="13" width="374" height="274" fill="none" stroke="{deep}" stroke-width="0.8" opacity="0.5"/>'
                f'<path d="M0 250 Q70 180 130 215 Q190 248 235 200 Q280 156 340 190 Q372 206 400 188 V300 H0 Z" fill="{mid}" opacity="0.55"/>'
                f'<path d="M30 70 q40 -18 84 -6 q50 14 60 52 q-36 22 -86 12 q-50 -10 -62 -34 q-4 -14 4 -24 Z" fill="{deep}" opacity="0.14"/>'
                f'<path d="M60 240 q60 -30 120 -10" stroke="{deep}" stroke-width="1.4" stroke-dasharray="5 4" fill="none"/>'
                f'{pois}'
                f'<g transform="translate(350,245)"><circle r="16" fill="none" stroke="{deep}" stroke-width="1.6"/><path d="M0 -14 L4 0 L0 14 L-4 0 Z" fill="{accent}"/><text x="-4" y="-20" font-size="11" font-family="Georgia" fill="{deep}">N</text></g>'
                + (f'<text x="20" y="282" font-size="10.5" font-family="Georgia" font-style="italic" fill="{deep}" opacity="0.85">shadowed regions = blockers · dotted route = current sprint · horizon = deadline</text>' if fantasy else ""))
    else:  # title-card
        body = (f'<rect width="400" height="300" fill="url(#sky)"/>{stars}'
                f'<ellipse cx="200" cy="160" rx="170" ry="70" fill="url(#glow)" opacity="0.6"/>'
                f'<path d="M0 226 Q100 200 200 222 T400 218 V300 H0 Z" fill="{deep}"/>'
                f'<line x1="60" y1="120" x2="340" y2="120" stroke="{accent}" stroke-width="1.4" opacity="0.9"/>'
                f'<line x1="60" y1="186" x2="340" y2="186" stroke="{accent}" stroke-width="1.4" opacity="0.9"/>'
                f'<circle cx="200" cy="120" r="3.4" fill="{accent}"/><circle cx="200" cy="186" r="3.4" fill="{accent}"/>')
    text_fill = deep if kind == "map" else light
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">{defs}{body}'
           f'<text x="50%" y="{286 if kind != "title-card" else 160}" text-anchor="middle" '
           f'font-family="Georgia" font-size="{15 if kind != "title-card" else 21}" '
           f'letter-spacing="1.5" fill="{text_fill if kind != "title-card" else accent}">{label}</text></svg>')
    path.write_text(svg, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", action="store_true")
    args = ap.parse_args()

    a = survey(args.preset)
    out = HERE / "output" / a["title_seed"].replace(" ", "-")
    title = scaffold_project(a, out)

    rng = random.Random(a["title_seed"])
    npcs = [(n, r, m) for n, r, m in zip(rng.sample(NAMES, 4), rng.sample(ROLES, 4), rng.sample(MOTIVES, 4))]

    model = ModelClient()
    print(f"\n✍️  Writing campaign (content tier: {model.mode}) …")
    prose = None
    if model.mode != "offline":
        prose = llm_campaign(model, a, title, npcs)
    if not prose:
        prose = template_campaign(a, title, npcs, rng)
    (out / "CAMPAIGN.md").write_text(prose, encoding="utf-8")
    print(f"📜 Campaign '{title}' → {out / 'CAMPAIGN.md'} ({len(prose.split())} words)")

    gov = AssetGovernor(out)
    pal = PALETTES.get(a["tone"], PALETTES["heroic"])
    assets = out / "assets"
    assets.mkdir(exist_ok=True)
    requests = ([("cover", f"{title}")]
                + [("portrait", f"{n} the {r}") for n, r, _ in npcs]
                + [("map", "Greyharbor & the Drowned Coast"),
                   ("title-card", f"Session One — {title}"),
                   ("portrait", f"{npcs[0][0]} alternate outfit"),
                   ("video", "Animated intro flythrough of Greyharbor")])

    print("\n🎨 Asset generation (governed by ASSET_POLICY.md):")
    for kind, prompt in requests:
        d = gov.check(kind, prompt)
        tag = {"ACCEPT": "✅", "WARN": "⚠️ ", "BLOCK": "🚫"}[d["verdict"]]
        print(f"  {tag} {d['verdict']:6} {kind:10} ${d['estimated_cost_usd']:.2f}  {prompt[:46]}"
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
