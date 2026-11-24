# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The looks of the grid (config key "theme", the Look menu in the grid,
or Settings > Look).

"classic" is the original look: the base CSS in __init__.py as it is.
"modern" is the same page with a softer, flatter style layered on top:
rounder tiles, borderless buttons and cards, a fresher green scale.
"gems" and "seal" use the modern shapes with other colour ladders:
  gems  peach, sky, blue, violet, then gold for mastered
  seal  rice paper, pale jade, jade, ink blue, then a cinnabar seal
        stamp (印章) for mastered
The colours of each status live here too, so the deck-list summary matches.

"modern" is the default. Every look is put in the page, so the Look menu
switches instantly; the choice is saved in the add-on's config.
"""

from __future__ import annotations

# Status colours (learning, young, mature, well known, mastered) for the
# deck-list bars.
CLASSIC_COLOURS = {1: "#f2c14e", 2: "#9fd59a", 3: "#2f8f57", 4: "#1b6b80", 5: "#17472c"}
MODERN_COLOURS = {1: "#fde68a", 2: "#a7f3d0", 3: "#10b981", 4: "#0e7490", 5: "#065f46"}

GEMS_COLOURS = {1: "#fdba74", 2: "#bfdbfe", 3: "#3b82f6", 4: "#7c3aed", 5: "#f59e0b"}
SEAL_COLOURS = {1: "#ecdcb9", 2: "#c6e3cf", 3: "#3f8f6b", 4: "#2b3a55", 5: "#b8322a"}

# Rules that override the base CSS (same selectors, placed after it).
# The shapes, shared by every look except classic.
MODERN_SHAPES = """
body { font-size: 14px; }
h2 { font-weight: 600; }
.counts .week { color: #047857; background: #d1fae5; padding: .05em .55em; border-radius: 1em; }
.switch span, .switch button, .tools span.pill {
  border: none; background: var(--canvas-inset, #eef0f3); padding: .3em .85em; font-weight: 500;
}
.switch .label, .tools .label { background: none; font-weight: normal; }
.switch .settings { background: var(--canvas-inset, #eef0f3); }
.switch span.on, .tools span.on { background: var(--button-primary-bg, #2f6fed); color: #fff; }
.tools input { border: none; background: var(--canvas-inset, #eef0f3); padding: .3em .8em; }
.bar { height: 8px; border-radius: 4px; }
.grid, .next { gap: 4px; }
.tile { border-radius: 8px; font-weight: 500; transition: transform .08s; }
.tile:hover { outline: none; box-shadow: 0 0 0 2px var(--button-primary-bg, #2f6fed); transform: translateY(-1px); }
.tile.weak::after { width: 7px; height: 7px; top: 3px; right: 3px; box-shadow: 0 0 0 2px var(--canvas, white); }
#tip { border: none; border-radius: 10px; box-shadow: 0 6px 24px rgba(0, 0, 0, .18); }
.hz b { color: #e11d48; }
#panel .box { border-radius: 14px; }
#panel .pbtn button { border: none; background: var(--canvas-inset, #eef0f3); font-weight: 500; }
.gp { border: none; background: var(--canvas-inset, #f4f5f7); border-radius: 10px; }
.gp .body { border-top: 1px solid rgba(128, 128, 128, .15); }
.mw { border: none; background: var(--canvas-inset, #f4f5f7); border-radius: 12px; }
.mw summary { background: transparent; border-left: none; }
.mw[open] summary { border-bottom: 1px solid rgba(128, 128, 128, .15); }
.lv { border-top: 1px solid rgba(128, 128, 128, .12); }
"""

MODERN_STATUS = """
.s0 { border: none; background: var(--border-subtle, #e2e5e9); color: var(--fg-subtle, #6b7280); }
.s1 { background: #fde68a; color: #713f12; }
.s2 { background: #a7f3d0; color: #064e3b; }
.s3 { background: #10b981; color: #fff; }
.s4 { background: #0e7490; color: #fff; }
.tile.s4 { background: linear-gradient(to top, #fcd34d 3px, #0e7490 3px); }
.s5 { background: #065f46; color: #fcd34d; }
"""

GEMS_STATUS = """
.s0 { border: none; background: var(--border-subtle, #e2e5e9); color: var(--fg-subtle, #6b7280); }
.s1, .tile.s1 { background: #fed7aa; color: #7c2d12; }
.s2, .tile.s2 { background: #bfdbfe; color: #1e3a8a; }
.s3, .tile.s3 { background: #3b82f6; color: #fff; }
.s4, .tile.s4 { background: #7c3aed; color: #fff; }
.s5 { background: #f59e0b; color: #451a03; }
.tile.s5 { background: linear-gradient(135deg, #fde68a, #f59e0b 70%); color: #451a03; font-weight: 700; }
.counts .week { color: #6d28d9; background: #ede9fe; }
.hz b { color: #7c3aed; }
"""

SEAL_STATUS = """
.s0 { border: none; background: var(--border-subtle, #e7e2d8); color: var(--fg-subtle, #7c7466); }
.s1, .tile.s1 { background: #f2e6c9; color: #6b4f1d; }
.s2, .tile.s2 { background: #c6e3cf; color: #1d4d33; }
.s3, .tile.s3 { background: #3f8f6b; color: #fff; }
.s4, .tile.s4 { background: #2b3a55; color: #f2e6c9; }
.s5 { background: #b8322a; color: #ffe9a8; }
/* Mastered: a red seal stamp, with a thin pale frame inside. */
.tile.s5 { background: #b8322a; color: #ffe9a8; outline: 1.5px solid rgba(255, 233, 168, .6); outline-offset: -4px; font-weight: 700; }
.counts .week { color: #8f2a22; background: #f6e1d6; }
.hz b { color: #b8322a; }
"""

THEMES = {
    "modern": {"css": MODERN_SHAPES + MODERN_STATUS, "colours": MODERN_COLOURS},
    "gems": {"css": MODERN_SHAPES + GEMS_STATUS, "colours": GEMS_COLOURS},
    "seal": {"css": MODERN_SHAPES + SEAL_STATUS, "colours": SEAL_COLOURS},
    "classic": {"css": "", "colours": CLASSIC_COLOURS},
}
THEME_CHOICES = [
    ("modern", "Modern"),
    ("gems", "Gems"),
    ("seal", "Seal"),
    ("classic", "Classic"),
]
DEFAULT_THEME = "modern"


def theme(config: dict) -> dict:
    return THEMES.get(config.get("theme", DEFAULT_THEME), THEMES[DEFAULT_THEME])
