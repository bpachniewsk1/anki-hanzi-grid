# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""A small summary of your progress on Anki's deck list (the main screen).

Anki lets add-ons add HTML under the deck list through the
`deck_browser_will_render_content` hook. Several popular add-ons (Review
Heatmap, Leaderboard …) use the same hook; each one appends its own block,
so they stack and don't conflict.

The deck list is redrawn often (after every review session and sync), and
reading the whole collection each time would slow Anki down. So the summary
is built once in the background and cached; it's rebuilt only when the
collection or the settings change. While it's being built, the deck list
shows a short "loading" line and is redrawn when the numbers are ready.
"""

from __future__ import annotations

import json
from html import escape

from aqt import gui_hooks, mw
from aqt.operations import QueryOp

from . import grid_data, themes

# Set by setup(): the functions from __init__.py we need.
_open_grid = None
_collect = None  # collect(config) -> Grid, run in a background thread

# The cached summary: the key it was built for, and its HTML.
_cache: dict = {"key": None, "html": ""}
_building = False

STATUSES = (grid_data.LEARNING, grid_data.YOUNG, grid_data.MATURE, grid_data.WELL_KNOWN, grid_data.MASTERED)

# All class names start with "hg-" so they can't clash with Anki's own
# styles or with other add-ons on the same page.
CSS = """
.hg-widget { display: inline-block; text-align: left; margin-top: 1.2em; font-size: 13px; }
.hg-widget table { border-collapse: collapse; }
.hg-widget td { padding: .15em .5em .15em 0; white-space: nowrap; }
.hg-widget .hg-head { margin-bottom: .3em; }
.hg-widget .hg-head a { margin-left: .6em; }
.hg-widget .hg-bar {
  display: flex; width: 12em; height: 8px; border-radius: 4px; overflow: hidden;
  background: var(--canvas-inset, #e6e6e6);
}
.hg-widget .hg-bar div { height: 100%; }
.hg-widget .hg-num { color: var(--fg-subtle, gray); }
.hg-widget .hg-week { color: #2f8f57; font-weight: bold; }
.hg-widget.hg-modern .hg-bar { height: 7px; }
.hg-widget.hg-modern .hg-week { color: #047857; }
"""


def setup(open_grid, collect) -> None:
    """Called once from __init__.py. `open_grid()` opens the grid window;
    `collect(config)` reads the collection (used in a background thread)."""
    global _open_grid, _collect
    _open_grid, _collect = open_grid, collect
    gui_hooks.deck_browser_will_render_content.append(on_deck_browser_render)
    gui_hooks.webview_did_receive_js_message.append(on_js_message)


def config_for_widget() -> dict:
    # __name__ is "<addon folder>.deck_widget"; Anki wants the folder.
    return mw.addonManager.getConfig(__name__.split(".")[0])


def cache_key(config: dict):
    """The summary is valid as long as neither the collection nor the
    settings have changed. `mod` in the col table changes on every
    review, edit and sync."""
    return (mw.col.db.scalar("select mod from col"), json.dumps(config, sort_keys=True))


def on_deck_browser_render(deck_browser, content) -> None:
    config = config_for_widget()
    if not config.get("deck_widget", True):
        return
    key = cache_key(config)
    if _cache["key"] == key:
        content.stats += _cache["html"]
        return
    content.stats += "<div class='hg-widget'><span class='hg-num'>Hanzi Grid: counting…</span></div>"
    start_build(key, config)


def start_build(key, config: dict) -> None:
    """Build the summary in the background, then redraw the deck list."""
    global _building
    if _building:
        return
    _building = True

    def done(grid: grid_data.Grid) -> None:
        global _building
        _building = False
        _cache["key"] = key
        _cache["html"] = widget_html(grid, config)
        if mw.state == "deckBrowser":
            mw.deckBrowser.refresh()

    def failed(error: Exception) -> None:
        global _building
        _building = False
        # A wrong setting (e.g. a renamed deck): say so instead of
        # retrying on every redraw. The grid window explains the problem.
        _cache["key"] = key
        _cache["html"] = (
            "<div class='hg-widget'><span class='hg-num'>Hanzi Grid: "
            f"{escape(str(error))}</span></div>"
        )
        if mw.state == "deckBrowser":
            mw.deckBrowser.refresh()

    QueryOp(parent=mw, op=lambda col: _collect(config), success=done).failure(failed).run_in_background()


def widget_html(grid: grid_data.Grid, config: dict, now_ms: int | None = None) -> str:
    """One row per level: label, a small bar, "studied / total · mature · well known" (when any)."""
    import time

    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    words = config.get("view", "chars") == "words"
    groups = grid.words if words else grid.chars
    colours = themes.theme(config)["colours"]
    modern = config.get("theme", themes.DEFAULT_THEME) != "classic"  # modern shapes
    rows = []
    total_week = 0
    for label, items in groups:
        total = len(items)
        counts = {s: 0 for s in STATUSES}
        week = 0
        for item in items:
            if item.status in counts:
                counts[item.status] += 1
            if item.studied_at is not None and item.studied_at >= now_ms - grid_data.WEEK_MS:
                week += 1
        total_week += week
        studied = sum(counts.values())
        mature = counts[grid_data.MATURE] + counts[grid_data.WELL_KNOWN] + counts[grid_data.MASTERED]
        well_known = counts[grid_data.WELL_KNOWN] + counts[grid_data.MASTERED]
        bar = "".join(
            f"<div style='width:{100 * counts[s] / total if total else 0:.2f}%;background:{colours[s]}'></div>"
            for s in reversed(STATUSES)
        )
        well_known_text = f" · {well_known} well known" if well_known else ""
        rows.append(
            f"<tr><td>{escape(label)}</td><td><div class='hg-bar'>{bar}</div></td>"
            f"<td class='hg-num'>{studied} / {total} · {mature} mature{well_known_text}</td></tr>"
        )
    week_text = f" <span class='hg-week'>+{total_week} this week</span>" if total_week else ""
    what = "words" if words else "characters"
    return (
        f"<div class='hg-widget{' hg-modern' if modern else ''}'><style>{CSS}</style>"
        f"<div class='hg-head'><b>Hanzi Grid</b> · {what}{week_text}"
        "<a href='#' onclick=\"pycmd('hanzi_grid:open'); return false;\">Open</a></div>"
        f"<table>{''.join(rows)}</table></div>"
    )


def on_js_message(handled, message: str, context):
    """The Open link runs pycmd('hanzi_grid:open') in the deck list."""
    if message == "hanzi_grid:open":
        _open_grid()
        return (True, None)
    return handled
