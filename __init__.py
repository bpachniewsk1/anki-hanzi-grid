# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Hanzi Grid: one screen showing every Chinese character in your collection,
grouped by HSK level and coloured by how well you know it.

Open it with Tools > Hanzi Grid. Hover a character for its pinyin and
meaning. Click it to see the answer side of the cards of every word that
contains it; Shift+click to find them in the Browser instead.

How the add-on is split up
--------------------------
- grid_data.py  reads the collection and works out the groups (no UI).
- __init__.py   (this file) adds the menu item, runs grid_data in the
                background, and shows the result in a window.
- previewer.py  the card preview window (built on Anki's own previewer).
- settings.py   the Settings window (decks, level source, fields …).
- data/hsk3.1/  the official HSK 3.1 character lists (see SOURCE.md there).
- config.json   default settings; you can edit them under
                Tools > Add-ons > Hanzi Grid > Config. config.md is the help
                text Anki shows next to that editor.
"""

from __future__ import annotations

import os
from html import escape

import aqt
from anki.collection import SearchNode
from aqt import mw
from aqt.operations import QueryOp
from aqt.qt import QAction, QDialog, QVBoxLayout, qconnect
from aqt.utils import disable_help_button, restoreGeom, saveGeom, showWarning, tooltip
from aqt.webview import AnkiWebView

# A relative import: Anki loaded this folder as a package, so we can import
# our other file from it.
from . import grid_data
from .previewer import CharPreviewer
from .settings import SettingsDialog, selected_decks

# Folder with the official HSK 3.1 character lists, next to this file.
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data", "hsk3.1")

# The two ways to give characters a level (config key "levels").
OFFICIAL = "hsk3.1"
FROM_DECK = "deck"

# Text and colour class for each status, used for the legend and the tiles.
STATUS_NAMES = {
    grid_data.UNSEEN: "Not studied",
    grid_data.LEARNING: "Learning",
    grid_data.YOUNG: "Young",
    grid_data.MATURE: "Mature",
}

CSS = """
body { margin: 1em 1.5em; }
.legend span { margin-right: 1.2em; }
.legend .tile { display: inline-flex; width: 1.2em; height: 1.2em; font-size: 14px; vertical-align: middle; margin-right: .3em; cursor: default; }
h2 { margin: 1.6em 0 .3em; font-size: 1.1em; }
.counts { color: var(--fg-subtle, gray); font-size: .9em; margin: .3em 0 .6em; }
.note { color: var(--fg-subtle, gray); font-size: .9em; max-width: 40em; }
.switch { margin: .8em 0 .2em; }
.switch span, .switch button {
  display: inline-block; padding: .2em .7em; margin-right: .3em; cursor: pointer;
  border: 1px solid var(--border-subtle, #ccc); border-radius: 1em;
}
.switch .settings { float: right; background: none; color: inherit; font: inherit; }
.switch span.on { background: var(--fg, black); color: var(--canvas, white); cursor: default; }

/* Progress bar: one coloured segment per status, side by side. Whatever
   is left over shows the grey track (= not studied yet). */
.bar {
  display: flex; height: 10px; border-radius: 5px; overflow: hidden;
  background: var(--canvas-inset, #e6e6e6); max-width: 40em;
}
.bar > div { height: 100%; }

.grid { display: flex; flex-wrap: wrap; gap: 3px; }
.tile {
  width: 1.7em; height: 1.7em; font-size: 22px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
}
.tile:hover { outline: 2px solid var(--fg, black); }

/* The hover box with pinyin and meaning. It's one box for the whole page,
   moved next to whichever character the mouse is over (see JS below). */
#tip {
  position: fixed; display: none; z-index: 10; max-width: 22em; pointer-events: none;
  padding: .5em .8em; border-radius: 6px; font-size: 14px;
  background: var(--canvas-elevated, white); color: var(--fg, black);
  border: 1px solid var(--border, #bbb); box-shadow: 0 2px 10px rgba(0, 0, 0, .25);
}
#tip .hz { font-size: 26px; font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; }
#tip .hz b { color: #c0392b; }
#tip .py { font-size: 17px; margin-left: .4em; }
#tip .mn { margin-top: .2em; }
#tip .ft { margin-top: .4em; color: var(--fg-subtle, gray); font-size: 12px; }

/* Status colours, shared by tiles and progress bars. */
.s0 { border: 1px solid var(--border-subtle, #ccc); color: var(--fg-subtle, gray); }
.s1 { background: #f2c14e; color: #222; }
.s2 { background: #9fd59a; color: #222; }
.s3 { background: #2f8f57; color: #fff; }
"""

# Clicks are sent to Python with pycmd(), Anki's bridge from the web page
# back to Python. One listener on the whole page handles every click:
# - buttons carry their command in data-cmd ("settings", "levels:deck" …)
# - tiles: click = preview, Shift+click = Browser.
# Hovering a tile copies its data-tip (HTML built in Python, already
# escaped) into the #tip box and places the box below the tile, or above
# it near the bottom of the window.
JS = """
const tip = document.getElementById("tip");
document.addEventListener("mouseover", (event) => {
  const tile = event.target.closest(".grid .tile");
  if (!tile) return (tip.style.display = "none");
  tip.innerHTML = tile.dataset.tip;
  tip.style.display = "block";
  const box = tile.getBoundingClientRect();
  const left = Math.min(box.left, window.innerWidth - tip.offsetWidth - 8);
  let top = box.bottom + 6;
  if (top + tip.offsetHeight > window.innerHeight) top = box.top - tip.offsetHeight - 6;
  tip.style.left = Math.max(8, left) + "px";
  tip.style.top = top + "px";
});
document.addEventListener("scroll", () => (tip.style.display = "none"));

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-cmd]");
  if (button) return pycmd(button.dataset.cmd);
  const tile = event.target.closest(".grid .tile");
  if (!tile) return;
  const action = event.shiftKey ? "search:" : "preview:";
  pycmd(action + tile.textContent);
});
"""


# The switch at the top of the grid: (value, button text).
LEVEL_CHOICES = [
    (OFFICIAL, "Official HSK 3.1 list"),
    (FROM_DECK, "From my deck's words"),
]

# Shown under the switch, so it's always clear where the levels come from.
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
CLICK_HINT = (
    "Hover a character for its pinyin and meaning (from its own card, or "
    "else from the lowest-level word that uses it). Click it to see the "
    "answer side of its cards, Shift+click to open the Browser."
)


def percent(part: int, whole: int) -> float:
    return 100 * part / whole if whole else 0


def progress(statuses: list[int]) -> str:
    """A stacked bar (mature, young, learning) plus a line of numbers."""
    total = len(statuses)
    counts = {s: statuses.count(s) for s in STATUS_NAMES}
    segments = "".join(
        f"<div class='s{s}' style='width:{percent(counts[s], total):.2f}%' "
        f"title='{STATUS_NAMES[s]}: {counts[s]}'></div>"
        for s in (grid_data.MATURE, grid_data.YOUNG, grid_data.LEARNING)
    )
    studied = total - counts[grid_data.UNSEEN]
    mature = counts[grid_data.MATURE]
    numbers = (
        f"{studied} / {total} studied ({percent(studied, total):.0f}%) · "
        f"{mature} mature ({percent(mature, total):.0f}%)"
    )
    return f"<div class='bar'>{segments}</div><div class='counts'>{numbers}</div>"


def hover_html(tile: grid_data.Tile, levels: str) -> str:
    """The contents of the hover box for one character, e.g.

        学生 xué sheng        (the character in red)
        student
        Young · level from 学生
    """
    word = tile.word
    if word is None:
        head, pinyin, meaning = tile.char, "", "Not in the chosen decks."
    else:
        head, pinyin, meaning = escape(word.text), word.pinyin, word.meaning
        if word.text != tile.char:
            # Highlight the character inside the longer word (escape()
            # leaves Chinese characters alone, so replace() still finds it).
            head = head.replace(tile.char, f"<b>{tile.char}</b>")
    footer = STATUS_NAMES[tile.status]
    if levels == FROM_DECK and tile.level_word:
        footer += f" · level from {tile.level_word}"
    return (
        f"<div><span class='hz'>{head}</span><span class='py'>{escape(pinyin)}</span></div>"
        f"<div class='mn'>{escape(meaning)}</div>"
        f"<div class='ft'>{escape(footer)}</div>"
    )


def build_html(groups, config: dict) -> str:
    """Turn the groups from grid_data.collect() into an HTML page body."""
    levels = config.get("levels", OFFICIAL)  # OFFICIAL or FROM_DECK
    decks = selected_decks(config)
    parts = ["<div class='legend'>"]
    for status, name in STATUS_NAMES.items():
        parts.append(f"<span><span class='tile s{status}'></span>{name}</span>")
    parts.append("</div>")

    parts.append("<div class='switch'>")
    parts.append("<button class='settings' data-cmd='settings'>⚙ Settings</button>")
    parts.append("Levels: ")
    for value, text in LEVEL_CHOICES:
        if value == levels:
            parts.append(f"<span class='on'>{text}</span>")
        else:
            parts.append(f"<span data-cmd='levels:{value}'>{text}</span>")
    parts.append("</div>")
    deck_text = ", ".join(escape(d) for d in decks) if decks else "all decks"
    parts.append(
        f"<p class='note'>Decks: <b>{deck_text}</b><br>"
        f"{LEVEL_NOTES[levels]}<br>{CLICK_HINT}</p>"
    )

    parts.append("<h2>All levels</h2>")
    parts.append(progress([tile.status for _, tiles in groups for tile in tiles]))

    for label, tiles in groups:
        parts.append(f"<h2>{escape(label)}</h2>")
        parts.append(progress([tile.status for tile in tiles]))
        parts.append("<div class='grid'>")
        for tile in tiles:
            # The hover box's HTML goes in an attribute, so it's escaped a
            # second time here (the browser undoes that when reading it).
            hover = escape(hover_html(tile, levels), quote=True)
            parts.append(f"<span class='tile s{tile.status}' data-tip='{hover}'>{tile.char}</span>")
        parts.append("</div>")

    parts.append("<div id='tip'></div>")
    parts.append(f"<script>{JS}</script>")
    return "".join(parts)


class HanziGridDialog(QDialog):
    def __init__(self, groups, char_cards, config) -> None:
        super().__init__(mw)
        self.config = config
        self.char_cards = char_cards  # character -> card ids to preview
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
        self.web.stdHtml(build_html(groups, config), css=[], js=[], head=f"<style>{CSS}</style>", context=self)
        self.show()

    def on_bridge_cmd(self, cmd: str) -> None:
        """Called when the page runs pycmd("...")."""
        if cmd == "settings":
            open_settings()
        elif cmd.startswith("levels:"):
            self.config["levels"] = cmd[len("levels:"):]
            save_config(self.config)
        elif cmd.startswith("preview:"):
            self.open_preview(cmd[len("preview:"):])
        elif cmd.startswith("search:"):
            browser = aqt.dialogs.open("Browser", mw)
            browser.search_for(self.search_for_char(cmd[len("search:"):]))

    def search_for_char(self, char: str) -> str:
        """Browser search for cards in the chosen decks whose word contains
        `char`, like:  ("deck:Anki xiehanzi") Simplified:*学*

        SearchNode lets Anki build (and escape) the deck part, so deck names
        with special characters still work.
        """
        col = mw.col
        fields = " OR ".join(
            f'"{escape_search(field)}:*{char}*"' for field in self.config["hanzi_fields"]
        )
        decks = [SearchNode(deck=name) for name in selected_decks(self.config)]
        if not decks:
            return col.build_search_string(fields)
        return col.build_search_string(col.group_searches(*decks, joiner="OR"), fields)

    def open_preview(self, char: str) -> None:
        card_ids = self.char_cards.get(char)
        if not card_ids:
            # Possible with the official list: e.g. 著 is HSK 4 but no word
            # in the xiehanzi deck uses it.
            tooltip(f"No card in the chosen decks contains {char}.", parent=self)
            return
        # One preview window at a time: close the previous one first.
        if self.previewer is not None:
            self.previewer.close()
        self.previewer = CharPreviewer(char, card_ids, on_close=self.on_preview_closed)
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


def show_dialog(groups, char_cards, config) -> None:
    global dialog
    if dialog is not None and dialog.isVisible():
        dialog.reject()  # close the old window; the new one has fresh data
    dialog = HanziGridDialog(groups, char_cards, config)


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
    SettingsDialog(config, LEVEL_CHOICES, on_save=save_config).exec()


def open_grid() -> None:
    config = mw.addonManager.getConfig(__name__)
    decks = selected_decks(config)
    use_official = config.get("levels", OFFICIAL) == OFFICIAL

    # Reading ~10,000 notes takes a moment. QueryOp runs the work in a
    # background thread so Anki doesn't freeze, then calls `success` back on
    # the main thread, where it's safe to create windows.
    QueryOp(
        parent=mw,
        op=lambda col: grid_data.collect(
            col,
            hanzi_fields=config["hanzi_fields"],
            level_field=config["level_field"],
            mature_days=config["mature_days"],
            decks=decks,
            pinyin_field=config.get("pinyin_field", ""),
            meaning_fields=config.get("meaning_fields", []),
            official_levels=(
                grid_data.load_level_lists(DATA_FOLDER) if use_official else None
            ),
        ),
        # collect() returns (groups, char_cards)
        success=lambda result: show_dialog(*result, config),
    ).failure(on_failure).with_progress("Building Hanzi Grid…").run_in_background()


# Add "Hanzi Grid" to the Tools menu. Like hooks, this runs once at startup.
action = QAction("Hanzi Grid", mw)
qconnect(action.triggered, open_grid)
mw.form.menuTools.addAction(action)

# Make the "Config" button in Tools > Add-ons open our Settings window
# instead of Anki's raw JSON editor.
mw.addonManager.setConfigAction(__name__, open_settings)
