# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Hanzi Grid: one screen showing every Chinese character (or word) in your
collection, grouped by HSK level and coloured by how well you know it.

Open it with Tools > Hanzi Grid. Hover a tile for its pinyin and meaning.
In the Characters view, click a character to see every word that contains
it, grouped by level; in the Words view, click a word to see the answer
side of its card. Shift+click finds the cards in the Browser.

How the add-on is split up
--------------------------
- grid_data.py  reads the collection and works out the groups (no UI).
- __init__.py   (this file) adds the menu item, runs grid_data in the
                background, and shows the result in a window.
- previewer.py  the card preview window (built on Anki's own previewer).
- deck_widget.py the small progress summary on Anki's deck list.
- settings.py   the Settings window (decks, level source, fields …).
- themes.py     the Classic and Modern looks (colours and shapes).
- data/hsk3.1/  the official HSK 3.1 character lists (see SOURCE.md there).
- data/grammar/ the grammar points and notes for the Grammar view.
- data/classifiers/ which measure word each word takes (Measure words view).
- config.json   default settings; you can edit them under
                Tools > Add-ons > Hanzi Grid > Config. config.md is the help
                text Anki shows next to that editor.
"""

from __future__ import annotations

import json
import os
import time
from html import escape

import aqt
from anki.collection import SearchNode
from aqt import mw
from aqt.operations import QueryOp
from aqt.qt import QAction, QDialog, QVBoxLayout, qconnect
from aqt.utils import disable_help_button, openLink, restoreGeom, saveGeom, showWarning, tooltip
from aqt.webview import AnkiWebView

# A relative import: Anki loaded this folder as a package, so we can import
# our other file from it.
from . import deck_widget, grid_data, themes
from .previewer import CharPreviewer
from .settings import SettingsDialog, selected_decks

# Folder with the official HSK 3.1 character lists, next to this file.
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data", "hsk3.1")

# The two ways to give characters a level (config key "levels").
OFFICIAL = "hsk3.1"
FROM_DECK = "deck"

# The four views (config key "view").
CHARS = "chars"
WORDS = "words"
GRAMMAR = "grammar"
MEASURE = "measure"
READING = "reading"

# The measure-word data (see data/classifiers/SOURCE.md).
CLASSIFIER_FILE = os.path.join(os.path.dirname(__file__), "data", "classifiers", "classifiers.json")

# The grammar notes (see data/grammar/SOURCE.md).
GRAMMAR_FOLDER = os.path.join(os.path.dirname(__file__), "data", "grammar")
WIKI_URL = "https://resources.allsetlearning.com/chinese/grammar/"

WEEK_MS = grid_data.WEEK_MS

# How many "Next up" tiles to show under each level.
NEXT_UP = 12

# Text and colour class for each status, used for the legend and the tiles.
STATUS_NAMES = {
    grid_data.UNSEEN: "Not studied",
    grid_data.LEARNING: "Learning",
    grid_data.YOUNG: "Young",
    grid_data.MATURE: "Mature",
    grid_data.MASTERED: "Mastered",
}

CSS = """
body { margin: 1em 1.5em; }
.legend span { margin-right: 1.2em; white-space: nowrap; }
.legend .tile { display: inline-flex; width: 1.2em; height: 1.2em; min-width: 0; font-size: 14px; vertical-align: middle; margin-right: .3em; cursor: default; }
h2 { margin: 1.6em 0 .3em; font-size: 1.1em; }
h3 { margin: 1.2em 0 .3em; font-size: 1em; }
.counts { color: var(--fg-subtle, gray); font-size: .9em; margin: .3em 0 .6em; }
.counts .week { color: #2f8f57; font-weight: bold; }
.note { color: var(--fg-subtle, gray); font-size: .9em; max-width: 44em; }
.switch, .tools { margin: .8em 0 .2em; }
.switch span, .switch button, .tools span.pill {
  display: inline-block; padding: .2em .7em; margin-right: .3em; cursor: pointer;
  border: 1px solid var(--border-subtle, #ccc); border-radius: 1em;
}
.switch .label, .tools .label { border: none; padding-left: 0; cursor: default; margin-left: .6em; }
.switch .settings { float: right; background: none; color: inherit; font: inherit; }
.switch span.on, .tools span.on { background: var(--fg, black); color: var(--canvas, white); cursor: default; }
.tools input {
  font: inherit; padding: .2em .6em; margin-left: .6em; width: 11em;
  border: 1px solid var(--border-subtle, #ccc); border-radius: 1em;
  background: var(--canvas-elevated, white); color: var(--fg, black);
}

/* Progress bar: one coloured segment per status, side by side. Whatever
   is left over shows the grey track (= not studied yet). */
.bar {
  display: flex; height: 10px; border-radius: 5px; overflow: hidden;
  background: var(--canvas-inset, #e6e6e6); max-width: 40em;
}
.bar > div { height: 100%; }

.grid, .next { display: flex; flex-wrap: wrap; gap: 3px; }
.next { margin-bottom: .6em; align-items: center; }
.next .label { color: var(--fg-subtle, gray); font-size: .9em; margin-right: .4em; }
.tile {
  position: relative; height: 1.7em; min-width: 1.7em; font-size: 22px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
}
.tile.w { font-size: 18px; padding: 0 .4em; height: 1.9em; }
.tile:hover { outline: 2px solid var(--fg, black); }
.tile.hide { display: none; }

/* A red dot on tiles you keep forgetting. */
.tile.weak::after {
  content: ""; position: absolute; top: 2px; right: 2px; width: 6px; height: 6px;
  border-radius: 50%; background: #e0393e;
}

/* The Show filter hides tiles in the grids (not in the Next up rows). */
body[data-show="unseen"] .grid .tile:not(.s0) { display: none; }
body[data-show="progress"] .grid .tile:not(.s1):not(.s2) { display: none; }
body[data-show="mature"] .grid .tile:not(.s3):not(.s4) { display: none; }
body[data-show="weak"] .grid .tile:not(.weak) { display: none; }

/* The hover box with pinyin and meaning. It's one box for the whole page,
   moved next to whichever tile the mouse is over (see JS below). */
#tip {
  position: fixed; display: none; z-index: 30; max-width: 22em; pointer-events: none;
  padding: .5em .8em; border-radius: 6px; font-size: 14px;
  background: var(--canvas-elevated, white); color: var(--fg, black);
  border: 1px solid var(--border, #bbb); box-shadow: 0 2px 10px rgba(0, 0, 0, .25);
}
.hz { font-size: 26px; font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; }
.hz b { color: #c0392b; }
.py { font-size: 17px; margin-left: .4em; }
.mn { margin-top: .2em; }
.ft { margin-top: .4em; color: var(--fg-subtle, gray); font-size: 12px; }

/* The character panel: the words containing one character, by level. */
#panel {
  position: fixed; inset: 0; z-index: 20; display: none; align-items: flex-start;
  justify-content: center; padding: 3em 1em; background: rgba(0, 0, 0, .45); overflow: auto;
}
#panel .box {
  position: relative; width: 100%; max-width: 60em; max-height: calc(100vh - 6em); overflow: auto;
  padding: 1.2em 1.5em; border-radius: 10px;
  background: var(--canvas, white); color: var(--fg, black); box-shadow: 0 4px 30px rgba(0, 0, 0, .4);
}
#panel .close {
  position: absolute; top: .6em; right: .8em; font: inherit; font-size: 20px; line-height: 1;
  background: none; border: none; color: inherit; cursor: pointer;
}
#panel .pbtn { margin: .6em 0 .2em; }
#panel .pbtn button {
  font: inherit; padding: .2em .8em; margin-right: .4em; cursor: pointer;
  border: 1px solid var(--border-subtle, #ccc); border-radius: 1em; background: none; color: inherit;
}
#panel .mn { font-size: 15px; }

/* The Grammar view: one collapsible block per grammar point. */
.gp { margin: .25em 0; border: 1px solid var(--border-subtle, #ddd); border-radius: 6px; max-width: 52em; }
.gp.hide { display: none; }
.gp summary { padding: .4em .7em; cursor: pointer; display: flex; align-items: center; gap: .6em; }
.gp summary::-webkit-details-marker { display: none; }
.gp summary .tile { font-size: 16px; height: 1.6em; min-width: 1.6em; flex: none; }
.gp summary .tile.w { font-size: 14px; }
.gp summary .none { width: 1.6em; height: 1.6em; flex: none; }
.gp summary .pat { color: var(--fg-subtle, gray); font-size: .9em; margin-left: auto; white-space: nowrap; }
.gp .body { padding: .2em .9em .8em 1.1em; border-top: 1px solid var(--border-subtle, #eee); }
.gp .body p { margin: .5em 0; max-width: 46em; }
.gp table { border-collapse: collapse; margin: .4em 0; }
.gp td { padding: .15em .9em .15em 0; vertical-align: top; }
.gp td.zh { font-size: 19px; font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; white-space: nowrap; }
.gp td.py { color: var(--fg-subtle, gray); white-space: nowrap; }
.gp .links { margin-top: .4em; font-size: .9em; }
.gp .links a { margin-right: 1em; cursor: pointer; color: var(--fg-link, #0a66c2); text-decoration: underline; }
.gp .todo { color: var(--fg-subtle, gray); font-style: italic; }
.gcount { color: var(--fg-subtle, gray); font-size: .9em; margin: .2em 0 .5em; }

/* The Measure words view: one collapsible block per measure word, with
   a tinted heading, and inside it one row per level. */
.mw { margin: .8em 0; border: 1px solid var(--border-subtle, #ddd); border-radius: 8px; overflow: hidden; }
.mw.hide, .lv.hide { display: none; }
.mw summary {
  padding: .55em .9em; cursor: pointer; display: flex; align-items: center; gap: .7em; flex-wrap: wrap;
  background: var(--canvas-inset, #f1f1f1); border-left: 5px solid var(--fg-subtle, #999);
}
.mw[open] summary { border-bottom: 1px solid var(--border-subtle, #ddd); }
.mw summary::-webkit-details-marker { display: none; }
.mw summary .tile { font-size: 20px; height: 1.6em; min-width: 1.6em; flex: none; }
.mw summary .hz { font-size: 24px; font-weight: bold; }
.mw summary .gloss { color: var(--fg-subtle, gray); font-size: .9em; }
.mw summary .pat { color: var(--fg-subtle, gray); font-size: .9em; margin-left: auto; white-space: nowrap; }
.mw .body { padding: .3em .9em .6em; }
.mw .bar { margin-top: .4em; }
.lv { display: flex; align-items: flex-start; gap: .8em; padding: .35em 0; border-top: 1px dashed var(--border-subtle, #e3e3e3); }
.lv .lvl { flex: none; width: 4.2em; padding-top: .45em; font-size: .85em; font-weight: bold; color: var(--fg-subtle, gray); }

/* The Reading view. */
.reading textarea {
  width: 100%; max-width: 60em; box-sizing: border-box; font: inherit; font-size: 16px; padding: .6em .8em;
  border: 1px solid var(--border-subtle, #ccc); border-radius: 6px; background: var(--canvas-elevated, white); color: var(--fg, black);
  font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
}
.rtext {
  max-width: 60em; font-size: 24px; line-height: 1.9; margin: .6em 0 1em;
  font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
}
.rtext .rw { cursor: pointer; border-radius: 4px; padding: 0 1px; }
.rtext .rw:hover { outline: 2px solid var(--fg, black); }
.rtext .rw > span { border-radius: 3px; padding: 0 1px; }
.rtext .s0, .rtext .rw > .s0 { border: none; background: var(--canvas-inset, #eee); color: var(--fg-subtle, gray); }
.rtext .nx { border-bottom: 2px dotted #e0393e; color: var(--fg-subtle, gray); }
.nxnote { color: #e0393e; }
.tile sup { font-size: .55em; margin-left: .15em; color: var(--fg-subtle, gray); }

/* Status colours, shared by tiles and progress bars. */
.s0 { border: 1px solid var(--border-subtle, #ccc); color: var(--fg-subtle, gray); }
.s1 { background: #f2c14e; color: #222; }
.s2 { background: #9fd59a; color: #222; }
.s3 { background: #2f8f57; color: #fff; }
.s4 { background: #17472c; color: #ffd866; }
"""

# Clicks are sent to Python with pycmd(), Anki's bridge from the web page
# back to Python. One listener on the whole page handles every click:
# - buttons carry their command in data-cmd ("settings", "view:words" …);
#   "close" is handled here (it closes the character panel);
# - tiles carry two commands: data-click, and data-shift for Shift+click;
# - the Show pills (data-show) and the Find box only filter in the page.
# Hovering a tile copies its data-tip (HTML built in Python, already
# escaped) into the #tip box and places the box below the tile, or above
# it near the bottom of the window.
# Python opens the character panel by calling showPanel(html).
JS = """
const tip = document.getElementById("tip");
const panel = document.getElementById("panel");
const panelBody = document.getElementById("panel-body");

function hideTip() { tip.style.display = "none"; }
document.addEventListener("mouseover", (event) => {
  const tile = event.target.closest("[data-tip]");
  if (!tile) return hideTip();
  tip.innerHTML = tile.dataset.tip;
  tip.style.display = "block";
  const box = tile.getBoundingClientRect();
  const left = Math.min(box.left, window.innerWidth - tip.offsetWidth - 8);
  let top = box.bottom + 6;
  if (top + tip.offsetHeight > window.innerHeight) top = box.top - tip.offsetHeight - 6;
  tip.style.left = Math.max(8, left) + "px";
  tip.style.top = top + "px";
});
document.addEventListener("scroll", hideTip, true);

function showPanel(html) {
  panelBody.innerHTML = html;
  panel.style.display = "flex";
  panel.querySelector(".box").scrollTop = 0;
}
function closePanel() { panel.style.display = "none"; hideTip(); }
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && panel.style.display === "flex") closePanel();
});

document.addEventListener("click", (event) => {
  if (event.target === panel) return closePanel();
  const button = event.target.closest("[data-cmd]");
  if (button) {
    if (button.dataset.cmd === "close") return closePanel();
    return pycmd(button.dataset.cmd);
  }
  const pill = event.target.closest(".pill[data-show]");
  if (pill) {
    document.body.dataset.show = pill.dataset.show;
    for (const p of document.querySelectorAll(".pill[data-show]")) p.classList.toggle("on", p === pill);
    return;
  }
  const tile = event.target.closest("[data-click]");
  if (!tile) return;
  hideTip();
  pycmd(event.shiftKey ? tile.dataset.shift : tile.dataset.click);
});

// The Find box: show only the tiles whose text contains what you typed.
// In the Characters view, typing a word (学生) also shows its characters.
// In the Grammar view it searches the titles, patterns and key words.
const find = document.getElementById("find");
if (find) find.addEventListener("input", () => {
  const query = find.value.trim();
  const view = document.body.dataset.view;
  if (view === "grammar") {
    const q = query.toLowerCase();
    for (const point of document.querySelectorAll(".gp")) {
      const text = point.querySelector("summary").textContent.toLowerCase();
      point.classList.toggle("hide", !!q && !text.includes(q));
    }
    return;
  }
  if (view === "measure") {
    // A measure word block matches by its heading (本, běn, "books"), and
    // then shows all its words; otherwise only the words that match are
    // shown, and empty rows and blocks are hidden.
    const q = query.toLowerCase();
    for (const block of document.querySelectorAll(".mw")) {
      const head = block.querySelector("summary").textContent.toLowerCase();
      const whole = !q || head.includes(q);
      let any = false;
      for (const row of block.querySelectorAll(".lv")) {
        let rowAny = false;
        for (const tile of row.querySelectorAll(".tile")) {
          const match = whole || tile.textContent.includes(query);
          tile.classList.toggle("hide", !match);
          rowAny = rowAny || match;
        }
        row.classList.toggle("hide", !rowAny);
        any = any || rowAny;
      }
      block.classList.toggle("hide", !any);
      if (q && any) block.open = true;
    }
    return;
  }
  for (const tile of document.querySelectorAll(".grid .tile")) {
    const text = tile.textContent;
    const match = !query || text.includes(query) || (view === "chars" && query.includes(text));
    tile.classList.toggle("hide", !match);
  }
});

// Expand / collapse every grammar point.
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-open]");
  if (!button) return;
  for (const point of document.querySelectorAll(".gp, .mw")) point.open = button.dataset.open === "1";
});
"""


# The switches at the top of the grid: (value, button text).
VIEW_CHOICES = [
    (CHARS, "Characters"),
    (WORDS, "Words"),
    (MEASURE, "Measure words"),
    (GRAMMAR, "Grammar"),
    (READING, "Reading"),
]
MEASURE_CHOICES = [
    ("classifier", "Measure word"),
    ("level", "HSK level"),
]
LEVEL_CHOICES = [
    (OFFICIAL, "Official HSK 3.1 list"),
    (FROM_DECK, "From my deck's words"),
]
SHOW_CHOICES = [
    ("all", "All"),
    ("unseen", "Not studied"),
    ("progress", "In progress"),
    ("mature", "Mature+"),
    ("weak", "Weak"),
]

# Shown under the switches, so it's always clear where the levels come from.
LEVEL_NOTES = {
    OFFICIAL: (
        "Levels come from the <b>official HSK 3.1 character list</b> (the "
        "2025 HSK syllabus)."
    ),
    FROM_DECK: (
        "These are <b>not official HSK character levels</b>. Each character "
        "gets the lowest HSK level of any word in the chosen decks that contains it. "
        "Hover a character to see that word."
    ),
}
WORD_LEVEL_NOTE = (
    "Word levels come from each note's HSK level field. Words without one "
    "are listed under Other."
)
MEASURE_NOTE = (
    "Which measure word (classifier) each word takes, from <b>CC-CEDICT</b> "
    "(CC BY-SA 4.0). It marks mainly concrete nouns; a word that isn't listed "
    "usually takes 个. The tile in each heading is the measure word itself, "
    "coloured by how well you know it. A word that takes several measure "
    "words (狗: 只 or 条) is listed under each."
)
READING_NOTE = (
    "Paste any Chinese text: every character is coloured by how well you "
    "know it, the words are matched against your decks, and the words you "
    "haven't studied are listed by level. Nothing leaves your computer."
)
GRAMMAR_NOTE = (
    "Grammar points from the <b>Chinese Grammar Wiki</b> (AllSet Learning, "
    "CC BY-NC-SA 4.0), grouped by the HSK levels the wiki aligns its bands to. "
    "Each point links to its article and has a short note with examples "
    "written for Hanzi Grid. The coloured tile shows how well you know the "
    "point's key character or word in your decks; hover it for pinyin and "
    "meaning, click it to find its cards."
)
CLICK_HINTS = {
    CHARS: (
        "Hover a character for its pinyin and meaning. Click it to see every "
        "word that contains it, by level; Shift+click to open the Browser. "
        "A red dot marks characters you keep forgetting."
    ),
    WORDS: (
        "Hover a word for its pinyin and meaning. Click it to see the answer "
        "side of its card; Shift+click to open the Browser. A red dot marks "
        "words you keep forgetting."
    ),
    GRAMMAR: "Click a grammar point to open it. Use Find to search by word or pattern.",
    MEASURE: (
        "Hover a word for its pinyin and meaning. Click it to see the answer "
        "side of its card; Shift+click to open the Browser."
    ),
    READING: (
        "Hover a word in the text for its pinyin and meaning. Click it to see "
        "its card; Shift+click to open the Browser. A dotted underline marks "
        "characters that are in none of your decks."
    ),
}

# A short text to try the Reading view with (written for the add-on).
SAMPLE_TEXT = (
    "我叫小明，今年二十岁，是一名大学生。我每天早上七点起床，先喝一杯咖啡，"
    "然后坐地铁去学校。我的专业是历史，虽然有点儿难，但是我很喜欢。\n"
    "周末的时候，我常常和朋友一起去公园跑步，或者在家看电影。上个月我去了北京，"
    "参观了长城和故宫，还吃了北京烤鸭，味道好极了。明年我想去上海工作，"
    "所以现在要努力学习，多练习听和说。"
)



def percent(part: int, whole: int) -> float:
    return 100 * part / whole if whole else 0


def progress(items, now_ms: int | None = None) -> str:
    """A stacked bar (mastered, mature, young, learning) plus a line of
    numbers, for a list of Tiles or Entries. Mastered counts as mature too.
    """
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    total = len(items)
    counts = {s: 0 for s in STATUS_NAMES}
    this_week = 0
    for item in items:
        counts[item.status] += 1
        if item.studied_at is not None and item.studied_at >= now_ms - WEEK_MS:
            this_week += 1
    segments = "".join(
        f"<div class='s{s}' style='width:{percent(counts[s], total):.2f}%' "
        f"title='{STATUS_NAMES[s]}: {counts[s]}'></div>"
        for s in (grid_data.MASTERED, grid_data.MATURE, grid_data.YOUNG, grid_data.LEARNING)
    )
    studied = total - counts[grid_data.UNSEEN]
    mastered = counts[grid_data.MASTERED]
    mature = counts[grid_data.MATURE] + mastered
    numbers = (
        f"{studied} / {total} studied ({percent(studied, total):.0f}%) · "
        f"{mature} mature ({percent(mature, total):.0f}%) · "
        f"{mastered} mastered ({percent(mastered, total):.0f}%)"
    )
    if this_week:
        numbers += f" · <span class='week'>+{this_week} this week</span>"
    return f"<div class='bar'>{segments}</div><div class='counts'>{numbers}</div>"


def head_html(text: str, pinyin: str, meaning: str, highlight: str = "") -> str:
    """The top of a hover box or panel: word, pinyin, meaning."""
    head = escape(text)
    if highlight and text != highlight:
        # Highlight the character inside the longer word (escape() leaves
        # Chinese characters alone, so replace() still finds it).
        head = head.replace(highlight, f"<b>{highlight}</b>")
    return (
        f"<div><span class='hz'>{head}</span><span class='py'>{escape(pinyin)}</span></div>"
        f"<div class='mn'>{escape(meaning)}</div>"
    )


def tile_hover(tile: grid_data.Tile, grid: grid_data.Grid, config: dict) -> str:
    """The hover box for one character, e.g.

        学生 xué sheng        (the character in red)
        student
        Young · level from 学生 · 3 / 12 words studied
    """
    word = tile.word
    if word is None:
        top = head_html(tile.char, "", "Not in the chosen decks.")
    else:
        top = head_html(word.text, word.pinyin, word.meaning, highlight=tile.char)
    footer = [STATUS_NAMES[tile.status]]
    if config.get("levels", OFFICIAL) == FROM_DECK and tile.level_word:
        footer.append(f"level from {tile.level_word}")
    if tile.words:
        studied = sum(1 for i in tile.words if grid.entries[i].status > grid_data.UNSEEN)
        footer.append(f"{studied} / {len(tile.words)} words studied")
    if tile.lapses >= config.get("weak_lapses", 3):
        footer.append(f"forgotten {tile.lapses}× ({tile.lapsed_word})")
    return top + f"<div class='ft'>{escape(' · '.join(footer))}</div>"


def entry_hover(entry: grid_data.Entry, config: dict) -> str:
    """The hover box for one word."""
    footer = [STATUS_NAMES[entry.status]]
    if entry.label:
        footer.append(entry.label)
    if entry.lapses >= config.get("weak_lapses", 3):
        footer.append(f"forgotten {entry.lapses}×")
    word = entry.word
    html = head_html(word.text, word.pinyin, word.meaning)
    if entry.classifiers:
        meta = load_classifiers()["meta"]
        parts = " · ".join(f"{c} ({meta.get(c, ['', ''])[0]})" if meta.get(c, ["", ""])[0] else c for c in entry.classifiers)
        html += f"<div class='mn'>measure word: {escape(parts)}</div>"
    return html + f"<div class='ft'>{escape(' · '.join(footer))}</div>"


def tile_html(text: str, status: int, hover: str, click: str, shift: str, weak: bool, word: bool) -> str:
    """One tile. The hover box's HTML goes in an attribute, so it's escaped
    a second time here (the browser undoes that when reading it)."""
    classes = f"tile s{status}" + (" w" if word else "") + (" weak" if weak else "")
    return (
        f"<span class='{classes}' data-tip='{escape(hover, quote=True)}' "
        f"data-click='{escape(click, quote=True)}' data-shift='{escape(shift, quote=True)}'>"
        f"{escape(text)}</span>"
    )


def char_tile_html(tile: grid_data.Tile, grid: grid_data.Grid, config: dict) -> str:
    weak = tile.status > grid_data.UNSEEN and tile.lapses >= config.get("weak_lapses", 3)
    return tile_html(
        tile.char, tile.status, tile_hover(tile, grid, config),
        f"char:{tile.char}", f"search:{tile.char}", weak, word=False,
    )


def entry_tile_html(entry: grid_data.Entry, config: dict, char: str = "") -> str:
    """A word tile. In the character panel (`char` given), clicking steps
    through that character's words starting at this one."""
    weak = entry.status > grid_data.UNSEEN and entry.lapses >= config.get("weak_lapses", 3)
    click = f"cards:{char}:{entry.card_id}" if char else f"card:{entry.card_id}"
    return tile_html(
        entry.word.text, entry.status, entry_hover(entry, config),
        click, f"search:{entry.word.text}", weak, word=True,
    )


def next_up_html(tiles_html: list[str]) -> str:
    if not tiles_html:
        return ""
    return "<div class='next'><span class='label'>Next up:</span>" + "".join(tiles_html) + "</div>"


def pills(choices, current: str, command: str) -> str:
    """A row of round buttons; the current one is filled in."""
    parts = []
    for value, text in choices:
        if value == current:
            parts.append(f"<span class='on'>{text}</span>")
        else:
            parts.append(f"<span data-cmd='{command}:{value}'>{text}</span>")
    return "".join(parts)


def build_html(grid: grid_data.Grid, config: dict) -> str:
    """Turn the Grid from grid_data.collect() into an HTML page body."""
    view = config.get("view", CHARS)
    levels = config.get("levels", OFFICIAL)  # OFFICIAL or FROM_DECK
    decks = selected_decks(config)
    weak_from = config.get("weak_lapses", 3)

    parts = ["<div class='legend'>"]
    for status, name in STATUS_NAMES.items():
        parts.append(f"<span><span class='tile s{status}'></span>{name}</span>")
    parts.append(f"<span><span class='tile s2 weak'></span>Weak (forgotten {weak_from}+ times)</span>")
    parts.append("</div>")

    parts.append("<div class='switch'>")
    parts.append("<button class='settings' data-cmd='settings'>⚙ Settings</button>")
    parts.append("<span class='label'>View:</span>" + pills(VIEW_CHOICES, view, "view"))
    if view == CHARS:
        parts.append("<span class='label'>Levels:</span>" + pills(LEVEL_CHOICES, levels, "levels"))
    if view == MEASURE:
        measure_by = config.get("measure_by", "classifier")
        parts.append("<span class='label'>Group by:</span>" + pills(MEASURE_CHOICES, measure_by, "measure_by"))
    parts.append("</div>")

    parts.append("<div class='tools'>")
    if view == GRAMMAR:
        parts.append("<span class='pill' data-open='1'>Expand all</span><span class='pill' data-open='0'>Collapse all</span>")
        parts.append("<span class='label'>Find:</span><input id='find' type='search' placeholder='过, 把, de, if …'>")
    elif view == READING:
        parts.append("<span class='pill' data-read='analyse'>Analyse</span><span class='pill' data-read='sample'>Sample text</span><span class='pill' data-read='clear'>Clear</span>")
    elif view == MEASURE:
        parts.append("<span class='pill' data-open='1'>Expand all</span><span class='pill' data-open='0'>Collapse all</span>")
        parts.append("<span class='label'>Show:</span>")
        for value, text in SHOW_CHOICES:
            on = " on" if value == "all" else ""
            parts.append(f"<span class='pill{on}' data-show='{value}'>{text}</span>")
        parts.append("<span class='label'>Find:</span><input id='find' type='search' placeholder='书 or 本'>")
    else:
        parts.append("<span class='label'>Show:</span>")
        for value, text in SHOW_CHOICES:
            on = " on" if value == "all" else ""
            parts.append(f"<span class='pill{on}' data-show='{value}'>{text}</span>")
        parts.append("<span class='label'>Find:</span><input id='find' type='search' placeholder='学 or 学生'>")
    parts.append("</div>")

    deck_text = ", ".join(escape(d) for d in decks) if decks else "all decks"
    level_note = {CHARS: LEVEL_NOTES[levels], WORDS: WORD_LEVEL_NOTE, GRAMMAR: GRAMMAR_NOTE, MEASURE: MEASURE_NOTE, READING: READING_NOTE}[view]
    parts.append(
        f"<p class='note'>Decks: <b>{deck_text}</b><br>{level_note}<br>{CLICK_HINTS[view]}</p>"
    )

    if view in (GRAMMAR, MEASURE, READING):
        if view == GRAMMAR:
            parts.append(grammar_html(grid, config))
        elif view == MEASURE:
            parts.append(measure_html(grid, config))
        else:
            parts.append(reading_html(grid, config))
        parts.append("<div id='tip'></div>")
        parts.append(f"<script>document.body.dataset.view = {json.dumps(view)};{JS}</script>")
        if view == READING:
            parts.append(f"<script>{READING_JS}</script>")
        return "".join(parts)

    if view == CHARS:
        groups = grid.chars

        def render(tile):
            return char_tile_html(tile, grid, config)

        def studyable(tile):
            return bool(tile.words)

    else:
        groups = grid.words

        def render(entry):
            return entry_tile_html(entry, config)

        def studyable(entry):
            return True

    now_ms = int(time.time() * 1000)
    parts.append("<h2>All levels</h2>")
    parts.append(progress([item for _, items in groups for item in items], now_ms))

    for label, items in groups:
        parts.append(f"<h2>{escape(label)}</h2>")
        parts.append(progress(items, now_ms))
        # The next tiles to learn: the first ones you haven't studied, in
        # deck order (frequency order in the xiehanzi deck).
        unseen = [i for i in items if i.status == grid_data.UNSEEN and studyable(i)]
        parts.append(next_up_html([render(i) for i in unseen[:NEXT_UP]]))
        parts.append("<div class='grid'>")
        parts.extend(render(item) for item in items)
        parts.append("</div>")

    parts.append(
        "<div id='panel'><div class='box'><button class='close' data-cmd='close' title='Close (Esc)'>×</button>"
        "<div id='panel-body'></div></div></div>"
    )
    parts.append("<div id='tip'></div>")
    # The Find box behaves differently per view (see JS).
    parts.append(f"<script>document.body.dataset.view = {json.dumps(view)};{JS}</script>")
    return "".join(parts)


_classifiers = None  # the classifier data once loaded


def load_classifiers() -> dict:
    """{"words": {word: [classifiers]}, "meta": {classifier: [pinyin, gloss]}}."""
    global _classifiers
    if _classifiers is None:
        with open(CLASSIFIER_FILE, encoding="utf-8") as file:
            _classifiers = json.load(file)
    return _classifiers


def classifier_head(classifier: str, grid: grid_data.Grid, config: dict) -> str:
    """A measure word's tile (its status in your decks), pinyin and gloss."""
    pinyin, gloss = load_classifiers()["meta"].get(classifier, ["", ""])
    return (
        key_tile_html(classifier, grid, config)
        + f"<span class='hz'>{escape(classifier)}</span><span class='py'>{escape(pinyin)}</span>"
        + f"<span class='gloss'>{escape(gloss)}</span>"
    )


def measure_html(grid: grid_data.Grid, config: dict) -> str:
    """The Measure words view: words grouped by the measure word they take
    (and by level inside), or by level and then measure word."""
    parts = []
    if config.get("measure_by", "classifier") == "level":
        for label, classifiers in grid_data.by_level_classifier(grid.entries):
            total = len({e.word.text for _, items in classifiers for e in items})
            parts.append(f"<h2>{escape(label)}</h2><div class='gcount'>{len(classifiers)} measure words · {total} words</div>")
            for classifier, items in classifiers:
                parts.append("<details class='mw' open><summary>")
                parts.append(classifier_head(classifier, grid, config))
                parts.append(f"<span class='pat'>{len(items)} words</span></summary><div class='body'>")
                parts.append(progress(items))
                parts.append(level_row(label, items, config))
                parts.append("</div></details>")
        return "".join(parts)

    groups = grid_data.by_classifier(grid.entries)
    with_cl = sum(1 for e in grid.entries if e.classifiers)
    parts.append(f"<div class='gcount'>{len(groups)} measure words · {with_cl} of {len(grid.entries)} words have one</div>")
    for classifier, levels in groups:
        items = [e for _, group in levels for e in group]
        general = classifier == grid_data.GENERAL_CLASSIFIER
        parts.append(f"<details class='mw'{'' if general else ' open'}><summary>")
        parts.append(classifier_head(classifier, grid, config))
        parts.append(f"<span class='pat'>{len(items)} words{' · the general measure word' if general else ''}</span></summary><div class='body'>")
        parts.append(progress(items))
        parts.extend(level_row(label, group, config) for label, group in levels)
        parts.append("</div></details>")
    return "".join(parts)


def level_row(label: str, entries, config: dict) -> str:
    """One row of a measure word block: the level on the left, its words
    on the right."""
    tiles = "".join(entry_tile_html(e, config) for e in entries)
    return f"<div class='lv'><span class='lvl'>{escape(label)}</span><div class='grid'>{tiles}</div></div>"


def reading_html(grid: grid_data.Grid, config: dict) -> str:
    """The Reading view: a text box, and the data the page needs to colour
    a text (every character's status, every word's status, level, pinyin,
    meaning and card), embedded as JSON for the JavaScript below."""
    chars = {char: tile.status for char, tile in grid.tiles.items()}
    words = {}
    for entry in grid.entries:
        text = entry.word.text
        if text and text not in words:
            words[text] = [entry.status, entry.label, entry.word.pinyin, entry.word.meaning, entry.card_id]
    longest = max((len(w) for w in words), default=1)
    data = json.dumps(
        {"chars": chars, "words": words, "longest": min(longest, 8), "names": STATUS_NAMES, "sample": SAMPLE_TEXT},
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return (
        "<div class='reading'>"
        "<textarea id='text' rows='7' placeholder='Paste Chinese text here, then click Analyse.'></textarea>"
        "<div id='stats' class='counts'></div>"
        "<div id='out' class='rtext'></div>"
        "<div id='learn'></div>"
        "</div>"
        f"<script>window.hgReading = {data};</script>"
    )


# The Reading view's script: splits the text into the longest words your
# decks know (greedy, left to right), colours every character, and lists
# the words you haven't studied, by level.
READING_JS = r"""
(() => {
  const data = window.hgReading;
  const box = document.getElementById("text");
  const out = document.getElementById("out");
  const stats = document.getElementById("stats");
  const learn = document.getElementById("learn");
  const isHanzi = (ch) => /[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/.test(ch);
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/'/g, "&#39;").replace(/"/g, "&quot;");

  function tip(word, info) {
    const [status, level, pinyin, meaning] = info;
    const foot = [data.names[status], level].filter(Boolean).join(" · ");
    return `<div><span class='hz'>${esc(word)}</span><span class='py'>${esc(pinyin)}</span></div>` +
      `<div class='mn'>${esc(meaning)}</div><div class='ft'>${esc(foot)}</div>`;
  }

  function analyse() {
    const text = box.value;
    try { localStorage.setItem("hanziGridText", text); } catch (e) {}
    const html = [];
    const seen = {};  // word -> count, for the list of words to learn
    let i = 0, charsTotal = 0, charsKnown = 0, charsMissing = 0, wordsTotal = 0, wordsKnown = 0;
    const byStatus = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0};
    while (i < text.length) {
      const ch = text[i];
      if (ch === "\n") { html.push("<br>"); i++; continue; }
      if (!isHanzi(ch)) { html.push(esc(ch)); i++; continue; }
      // The longest word starting here that your decks contain.
      let word = null;
      for (let len = Math.min(data.longest, text.length - i); len >= 1; len--) {
        const candidate = text.substr(i, len);
        if (data.words[candidate]) { word = candidate; break; }
      }
      if (word) {
        const info = data.words[word];
        wordsTotal++;
        if (info[0] > 0) wordsKnown++;
        seen[word] = (seen[word] || 0) + 1;
        let inner = "";
        for (const c of word) {
          const s = data.chars[c] ?? 0;
          charsTotal++; byStatus[s]++;
          if (s > 0) charsKnown++;
          inner += `<span class='s${s}'>${esc(c)}</span>`;
        }
        html.push(`<span class='rw' data-tip='${esc(tip(word, info))}' data-click='card:${info[4]}' data-shift='search:${esc(word)}'>${inner}</span>`);
        i += word.length;
      } else {
        charsTotal++;
        const s = data.chars[ch];
        if (s === undefined) { charsMissing++; byStatus[0]++; html.push(`<span class='rw nx'>${esc(ch)}</span>`); }
        else { byStatus[s]++; if (s > 0) charsKnown++; html.push(`<span class='rw s${s}' data-shift='search:${esc(ch)}' data-click='char:${esc(ch)}'>${esc(ch)}</span>`); }
        i++;
      }
    }
    out.innerHTML = html.join("");
    if (!charsTotal) { stats.textContent = ""; learn.innerHTML = ""; return; }
    const pct = (a, b) => b ? Math.round(100 * a / b) : 0;
    stats.innerHTML = `<b>${pct(charsKnown, charsTotal)}% of characters</b> studied (${charsKnown} / ${charsTotal})` +
      ` · <b>${pct(wordsKnown, wordsTotal)}% of words</b> studied (${wordsKnown} / ${wordsTotal})` +
      ` · mature or better: ${byStatus[3] + byStatus[4]} characters` +
      (charsMissing ? ` · <span class='nxnote'>${charsMissing} characters in none of your decks</span>` : "");
    // Words to learn: the matched words you haven't studied, by level,
    // most frequent in the text first.
    const groups = {};
    for (const word of Object.keys(seen)) {
      const info = data.words[word];
      if (info[0] > 0) continue;
      const level = info[1] || "Other";
      (groups[level] = groups[level] || []).push(word);
    }
    const levels = Object.keys(groups).sort((a, b) => (a === "Other") - (b === "Other") || a.localeCompare(b, undefined, {numeric: true}));
    if (!levels.length) { learn.innerHTML = "<h2>Words to learn</h2><p class='note'>You have studied every word in this text.</p>"; return; }
    let list = "<h2>Words to learn</h2>";
    for (const level of levels) {
      const words = groups[level].sort((a, b) => seen[b] - seen[a]);
      list += `<div class='lv'><span class='lvl'>${esc(level)}</span><div class='grid'>` + words.map((w) => {
        const info = data.words[w];
        return `<span class='tile w s0' data-tip='${esc(tip(w, info))}' data-click='card:${info[4]}' data-shift='search:${esc(w)}'>${esc(w)}` +
          (seen[w] > 1 ? `<sup>${seen[w]}</sup>` : "") + `</span>`;
      }).join("") + "</div></div>";
    }
    learn.innerHTML = list;
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-read]");
    if (!button) return;
    if (button.dataset.read === "sample") box.value = data.sample;
    if (button.dataset.read === "clear") box.value = "";
    analyse();
  });
  box.addEventListener("keydown", (event) => { if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) analyse(); });
  try { const saved = localStorage.getItem("hanziGridText"); if (saved) box.value = saved; } catch (e) {}
  analyse();
})();
"""


_grammar = None  # (index, points) once loaded


def load_grammar():
    """The grammar points (index.json) and notes (points.json)."""
    global _grammar
    if _grammar is None:
        with open(os.path.join(GRAMMAR_FOLDER, "index.json"), encoding="utf-8") as file:
            index = json.load(file)
        with open(os.path.join(GRAMMAR_FOLDER, "points.json"), encoding="utf-8") as file:
            points = {k: v for k, v in json.load(file).items() if not k.startswith("_")}
        _grammar = (index, points)
    return _grammar


def key_tile_html(key: str, grid: grid_data.Grid, config: dict) -> str:
    """The coloured tile for a grammar point's key character or word: its
    status in your decks, with the usual hover box and click."""
    if not key:
        return "<span class='none'></span>"
    tile = grid.tiles.get(key)
    if tile is not None:
        return char_tile_html(tile, grid, config)
    entry = next((e for e in grid.entries if e.word.text == key), None)
    if entry is not None:
        return entry_tile_html(entry, config)
    # Not in the decks at all: a plain grey tile.
    return f"<span class='tile s0 w'>{escape(key)}</span>"


def grammar_html(grid: grid_data.Grid, config: dict) -> str:
    """The Grammar view: every point by level, as collapsible blocks."""
    index, points = load_grammar()
    # Notes with their own url and level (not in the wiki index) join the
    # level they name.
    extra = {}
    for key, note in points.items():
        if "url" in note:
            extra.setdefault(note.get("level", 3), []).append((key, note))
    parts = []
    for band in index:
        items = [(p["id"], p["title"], points.get(p["id"])) for p in band["points"]]
        items += [(key, note.get("title", key), note) for key, note in extra.get(band["level"], [])]
        with_notes = sum(1 for _, _, note in items if note)
        parts.append(f"<h2>{escape(band['label'])} <span class='gcount'>({escape(band['cefr'])})</span></h2>")
        parts.append(f"<div class='gcount'>{len(items)} points · {with_notes} with notes</div>")
        for key, title, note in items:
            url = (note or {}).get("url") or WIKI_URL + key
            parts.append("<details class='gp'><summary>")
            parts.append(key_tile_html((note or {}).get("key", ""), grid, config))
            parts.append(f"<span>{escape(title)}</span>")
            if note:
                parts.append(f"<span class='pat'>{escape(note['pattern'])}</span>")
            parts.append("</summary><div class='body'>")
            if note:
                parts.append(f"<p>{escape(note['explain'])}</p><table>")
                for zh, py, en in note["examples"]:
                    parts.append(f"<tr><td class='zh'>{escape(zh)}</td><td class='py'>{escape(py)}</td><td>{escape(en)}</td></tr>")
                parts.append("</table>")
                if note.get("note"):
                    parts.append(f"<p>{escape(note['note'])}</p>")
            else:
                parts.append("<p class='todo'>No note written yet; the wiki article has the full explanation.</p>")
            parts.append("<div class='links'>")
            parts.append(f"<a data-cmd='link:{escape(url, quote=True)}'>Read on the Chinese Grammar Wiki ↗</a>")
            if note and note.get("key"):
                parts.append(f"<a data-cmd='search:{escape(note['key'], quote=True)}'>Find {escape(note['key'])} in the Browser</a>")
            parts.append("</div></div></details>")
    return "".join(parts)


def panel_html(tile: grid_data.Tile, grid: grid_data.Grid, config: dict) -> str:
    """The character panel: the character, then every word containing it,
    grouped by the words' HSK levels, each a tile coloured by status."""
    entries = [grid.entries[i] for i in tile.words]
    word = tile.word
    if word is None:
        top = head_html(tile.char, "", "")
    else:
        # The character's own note, or (highlighted) its lowest-level word.
        top = head_html(word.text, word.pinyin, word.meaning, highlight=tile.char)
    meta = [STATUS_NAMES[tile.status]]
    if tile.lapses >= config.get("weak_lapses", 3):
        meta.append(f"forgotten {tile.lapses}× ({tile.lapsed_word})")
    parts = [top, f"<div class='ft'>{escape(' · '.join(meta))}</div>"]
    parts.append(progress(entries))
    char_attr = escape(tile.char, quote=True)
    parts.append(
        "<div class='pbtn'>"
        f"<button data-cmd='cards:{char_attr}:'>Open all {len(entries)} cards</button>"
        f"<button data-cmd='search:{char_attr}'>Find in Browser</button>"
        "</div>"
    )

    groups = {}  # level number -> (label, [entries]); keeps the words' order
    other = []
    for entry in entries:
        if entry.level is not None:
            groups.setdefault(entry.level, (entry.label, []))[1].append(entry)
        else:
            other.append(entry)
    ordered = [groups[level] for level in sorted(groups)]
    if other:
        ordered.append(("Other", other))
    for label, items in ordered:
        parts.append(f"<h3>{escape(label)}</h3><div class='grid'>")
        parts.extend(entry_tile_html(entry, config, char=tile.char) for entry in items)
        parts.append("</div>")
    return "".join(parts)


class HanziGridDialog(QDialog):
    def __init__(self, grid: grid_data.Grid, config: dict) -> None:
        super().__init__(mw)
        self.config = config
        self.grid = grid
        self.previewer: CharPreviewer | None = None
        self.setWindowTitle("Hanzi Grid")
        disable_help_button(self)

        # AnkiWebView is Anki's web view (a small browser). Most of Anki's
        # own screens use it, and it comes with Anki's styling and night mode.
        self.web = AnkiWebView(parent=self, title="hanzi grid")
        self.web.set_bridge_command(self.on_bridge_cmd, self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)

        # Remember the window size between openings (stored in the profile).
        restoreGeom(self, "hanziGrid", default_size=(900, 700))
        # js=[] means: don't load jQuery, we don't need it.
        self.web.stdHtml(
            build_html(grid, config),
            css=[],
            js=[],
            head=f"<style>{CSS}{themes.theme(config)['css']}</style>",
            context=self,
        )
        self.show()

    def on_bridge_cmd(self, cmd: str) -> None:
        """Called when the page runs pycmd("...")."""
        if cmd == "settings":
            open_settings()
        elif cmd.startswith("levels:"):
            self.config["levels"] = cmd[len("levels:"):]
            save_config(self.config)
        elif cmd.startswith("view:"):
            self.config["view"] = cmd[len("view:"):]
            save_config(self.config)
        elif cmd.startswith("measure_by:"):
            self.config["measure_by"] = cmd[len("measure_by:"):]
            save_config(self.config)
        elif cmd.startswith("char:"):
            self.open_panel(cmd[len("char:"):])
        elif cmd.startswith("card:"):
            # A word tile in the Words view: preview that one card.
            card_id = int(cmd[len("card:"):])
            entry = next((e for e in self.grid.entries if e.card_id == card_id), None)
            self.open_preview(entry.word.text if entry else "Word", [card_id])
        elif cmd.startswith("cards:"):
            # "cards:学:<card id>" from the panel: every card of 学, starting
            # at that word ("cards:学:" starts at the first one).
            char, _, start = cmd[len("cards:"):].partition(":")
            tile = self.grid.tiles.get(char)
            if tile is None or not tile.words:
                return
            card_ids = [self.grid.entries[i].card_id for i in tile.words]
            index = card_ids.index(int(start)) if start and int(start) in card_ids else 0
            self.open_preview(char, card_ids, index)
        elif cmd.startswith("search:"):
            browser = aqt.dialogs.open("Browser", mw)
            browser.search_for(self.search_for_text(cmd[len("search:"):]))
        elif cmd.startswith("link:"):
            openLink(cmd[len("link:"):])

    def search_for_text(self, text: str) -> str:
        """Browser search for cards in the chosen decks whose word contains
        `text`, like:  ("deck:Anki xiehanzi") Simplified:*学*

        SearchNode lets Anki build (and escape) the deck part, so deck names
        with special characters still work.
        """
        col = mw.col
        fields = " OR ".join(
            f'"{escape_search(field)}:*{escape_search(text)}*"' for field in self.config["hanzi_fields"]
        )
        decks = [SearchNode(deck=name) for name in selected_decks(self.config)]
        if not decks:
            return col.build_search_string(fields)
        return col.build_search_string(col.group_searches(*decks, joiner="OR"), fields)

    def open_panel(self, char: str) -> None:
        tile = self.grid.tiles.get(char)
        if tile is None or not tile.words:
            # Possible with the official list: e.g. 著 is HSK 4 but no word
            # in the xiehanzi deck uses it.
            tooltip(f"No card in the chosen decks contains {char}.", parent=self)
            return
        html = panel_html(tile, self.grid, self.config)
        self.web.eval(f"showPanel({json.dumps(html)});")

    def open_preview(self, title: str, card_ids: list[int], index: int = 0) -> None:
        # One preview window at a time: close the previous one first.
        if self.previewer is not None:
            self.previewer.close()
        self.previewer = CharPreviewer(title, card_ids, on_close=self.on_preview_closed, index=index)
        self.previewer.open()

    def on_preview_closed(self) -> None:
        self.previewer = None

    def reject(self) -> None:
        # Runs when the window is closed (Esc or the close button).
        if self.previewer is not None:
            self.previewer.close()
        saveGeom(self, "hanziGrid")
        self.web.cleanup()
        super().reject()


# Keep a reference to the open window. Without one, Python could garbage-
# collect our dialog object while Qt is still showing it.
dialog: HanziGridDialog | None = None


def show_dialog(grid: grid_data.Grid, config: dict) -> None:
    global dialog
    if dialog is not None and dialog.isVisible():
        dialog.reject()  # close the old window; the new one has fresh data
    dialog = HanziGridDialog(grid, config)


def escape_search(text: str) -> str:
    """Escape characters that have a special meaning in Anki searches."""
    for special in ("\\", '"', "*", "_", ":"):
        text = text.replace(special, "\\" + special)
    return text


def on_failure(error: Exception) -> None:
    """Called if building the grid raised an exception."""
    if isinstance(error, ValueError):
        # Our own, expected problems, e.g. a deck in the settings was
        # renamed or deleted. Explain them in a normal message.
        showWarning(str(error))
    else:
        # Anything else is a bug: let Anki show its error window, so the
        # traceback can be reported.
        raise error


def save_config(config: dict) -> None:
    """Store the settings (in meta.json, via Anki) and rebuild the grid."""
    mw.addonManager.writeConfig(__name__, config)
    open_grid()


def open_settings() -> None:
    config = mw.addonManager.getConfig(__name__)
    SettingsDialog(config, LEVEL_CHOICES, themes.THEME_CHOICES, on_save=save_config).exec()


def collect(config: dict) -> grid_data.Grid:
    """Read the collection with the given settings. Runs in a background
    thread (see open_grid), so it must not touch the user interface."""
    use_official = config.get("levels", OFFICIAL) == OFFICIAL
    return grid_data.collect(
        mw.col,
        hanzi_fields=config["hanzi_fields"],
        level_field=config["level_field"],
        mature_days=config["mature_days"],
        decks=selected_decks(config),
        mastered_days=config.get("mastered_days", 90),
        pinyin_field=config.get("pinyin_field", ""),
        meaning_fields=config.get("meaning_fields", []),
        official_levels=grid_data.load_level_lists(DATA_FOLDER) if use_official else None,
        classifiers=load_classifiers()["words"],
    )


def open_grid() -> None:
    config = mw.addonManager.getConfig(__name__)

    # Reading ~10,000 notes takes a moment. QueryOp runs the work in a
    # background thread so Anki doesn't freeze, then calls `success` back on
    # the main thread, where it's safe to create windows.
    QueryOp(
        parent=mw,
        op=lambda col: collect(config),
        success=lambda grid: show_dialog(grid, config),
    ).failure(on_failure).with_progress("Building Hanzi Grid…").run_in_background()


# Add "Hanzi Grid" to the Tools menu. Like hooks, this runs once at startup.
action = QAction("Hanzi Grid", mw)
qconnect(action.triggered, open_grid)
mw.form.menuTools.addAction(action)

# Make the "Config" button in Tools > Add-ons open our Settings window
# instead of Anki's raw JSON editor.
mw.addonManager.setConfigAction(__name__, open_settings)

# The progress summary on the deck list.
deck_widget.setup(open_grid, collect)
