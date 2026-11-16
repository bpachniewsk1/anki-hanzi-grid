# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The two looks of the grid (config key "theme", Settings > Look).

"classic" is the original look: the base CSS in __init__.py as it is.
"modern" is the same page with a softer, flatter style layered on top:
rounder tiles, borderless buttons and cards, a fresher green scale. The
colours of each status live here too, so the deck-list summary matches.

Switching back is one setting: Look > Classic.
"""

from __future__ import annotations

# Status colours (learning, young, mature, mastered) for the deck-list bars.
CLASSIC_COLOURS = {1: "#f2c14e", 2: "#9fd59a", 3: "#2f8f57", 4: "#17472c"}
MODERN_COLOURS = {1: "#fde68a", 2: "#a7f3d0", 3: "#10b981", 4: "#065f46"}

# Rules that override the base CSS (same selectors, placed after it).
MODERN_CSS = """
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
.s0 { border: none; background: var(--border-subtle, #e2e5e9); color: var(--fg-subtle, #6b7280); }
.s1 { background: #fde68a; color: #713f12; }
.s2 { background: #a7f3d0; color: #064e3b; }
.s3 { background: #10b981; color: #fff; }
.s4 { background: #065f46; color: #fcd34d; }
"""

THEMES = {
    "classic": {"css": "", "colours": CLASSIC_COLOURS},
    "modern": {"css": MODERN_CSS, "colours": MODERN_COLOURS},
}
THEME_CHOICES = [
    ("modern", "Modern"),
    ("classic", "Classic"),
]


def theme(config: dict) -> dict:
    return THEMES.get(config.get("theme", "modern"), THEMES["modern"])
