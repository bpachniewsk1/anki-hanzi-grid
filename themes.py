# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The looks of the grid (config key "theme", the Look menu in the grid,
or Settings > Look).

  classic  the original look: the base CSS in __init__.py as it is.
  modern   softer and flatter (rounder tiles, borderless buttons), a
           fresh green scale. The default.
  seal     classic, with ink blue for well known and a red seal stamp
           (印章) for mastered.
  ink      ink on paper: greys from a light wash to black ink, mastered
           with a small red seal. Pairs well with the Kai font.
  clear    a colour-blind-safe ladder (viridis: yellow, green, teal,
           blue, purple) that also prints well in greyscale.

The colours of each status live here too, so the deck-list summary
matches. Every look is put in the page, so the Look menu switches
instantly; the choice is saved in the add-on's config.
"""

from __future__ import annotations

# Status colours (learning, young, mature, well known, mastered) for the
# deck-list bars.
CLASSIC_COLOURS = {1: "#f2c14e", 2: "#9fd59a", 3: "#2f8f57", 4: "#1b6b80", 5: "#17472c"}
MODERN_COLOURS = {1: "#fde68a", 2: "#a7f3d0", 3: "#10b981", 4: "#0e7490", 5: "#065f46"}

SEAL_COLOURS = {1: "#f2c14e", 2: "#9fd59a", 3: "#2f8f57", 4: "#2b3a55", 5: "#b8322a"}
INK_COLOURS = {1: "#e8dcc0", 2: "#cbc2b0", 3: "#7a7266", 4: "#3a3631", 5: "#141210"}
CLEAR_COLOURS = {1: "#fde725", 2: "#5ec962", 3: "#21918c", 4: "#3b528b", 5: "#440154"}

# Rules that override the base CSS (same selectors, placed after it).
# The modern shapes.
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

# Seal: the classic look (its shapes, font and first three colours) with
# ink blue for well known and a red seal stamp for mastered.
SEAL_CSS = """
.s4, .tile.s4 { background: #2b3a55; color: #f2e6c9; }
.s5 { background: #b8322a; color: #ffe9a8; }
/* Mastered: a red seal stamp, with a thin pale frame inside. */
.tile.s5 { outline: 1px solid rgba(255, 233, 168, .65); outline-offset: -4px; }
.tile.s5:hover { outline: 2px solid var(--fg, black); outline-offset: 0; }
.hz b { color: #b8322a; }
"""

# Ink: shades of ink on paper, a red seal on mastered. Pairs well with the
# Kai font (楷 in the Font switch).
INK_CSS = """
.s0 { border: 1px solid #d8d0c0; color: #a39a88; }
.s1, .tile.s1 { background: #e8dcc0; color: #5b4a2c; }
.s2, .tile.s2 { background: #cbc2b0; color: #2b2620; }
.s3, .tile.s3 { background: #7a7266; color: #fbf7ee; }
.s4, .tile.s4 { background: #3a3631; color: #fbf7ee; }
.s5 { background: #141210; color: #fff; }
/* Mastered: black ink with a small red seal in the corner. */
.tile.s5::before {
  content: ""; position: absolute; bottom: 3px; right: 3px; width: 6px; height: 6px;
  background: #c0392b; border-radius: 1px;
}
.counts .week { color: #8f2a22; }
.hz b { color: #c0392b; }
"""

# Clear: viridis, readable with any kind of colour blindness.
CLEAR_CSS = """
.s1, .tile.s1 { background: #fde725; color: #3d3500; }
.s2, .tile.s2 { background: #5ec962; color: #0b2e13; }
.s3, .tile.s3 { background: #21918c; color: #fff; }
.s4, .tile.s4 { background: #3b528b; color: #fff; }
.s5 { background: #440154; color: #fde725; }
.counts .week { color: #3b528b; }
"""

THEMES = {
    "modern": {"css": MODERN_SHAPES + MODERN_STATUS, "colours": MODERN_COLOURS},
    "seal": {"css": SEAL_CSS, "colours": SEAL_COLOURS},
    "ink": {"css": INK_CSS, "colours": INK_COLOURS},
    "clear": {"css": CLEAR_CSS, "colours": CLEAR_COLOURS},
    "classic": {"css": "", "colours": CLASSIC_COLOURS},
}
THEME_CHOICES = [
    ("modern", "Modern"),
    ("seal", "Seal"),
    ("ink", "Ink"),
    ("clear", "Clear"),
    ("classic", "Classic"),
]
DEFAULT_THEME = "modern"

# The hanzi font and size (config "font", "font_size"; the Font and Size
# switches next to Settings). The three styles a reader meets everywhere.
FONT_CHOICES = [
    ("hei", "黑", "Hei 黑体 (sans): apps, websites, signs"),
    ("song", "宋", "Song 宋体 (serif): books, newspapers, exam papers"),
    ("kai", "楷", "Kai 楷体 (brush): textbooks, stroke order, handwriting"),
]
SIZE_CHOICES = [
    ("s", "S", "Small"),
    ("m", "M", "Medium"),
    ("l", "L", "Large"),
]
DEFAULT_FONT = "hei"
DEFAULT_SIZE = "m"


def theme(config: dict) -> dict:
    return THEMES.get(config.get("theme", DEFAULT_THEME), THEMES[DEFAULT_THEME])
