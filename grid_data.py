# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Work out, for every Chinese character in your collection, how well you know
it and which HSK level it belongs to.

This file only talks to the collection (`col`). It doesn't import anything
from `aqt` (Anki's user interface), so it can be tested outside Anki, and it
can run in a background thread without touching the screen.
"""

from __future__ import annotations

import html
import os
import re
from typing import NamedTuple

# Unicode ranges for Chinese characters (CJK Unified Ideographs, Extension A,
# and Compatibility Ideographs). Anything else in a field (pinyin, HTML,
# punctuation, Latin letters) is ignored.
HANZI = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

# Fields can contain HTML such as <b>学</b> or <img src="...">. Removing the
# tags (everything between < and >) leaves just the text.
HTML_TAG = re.compile(r"<[^>]*>")


def strip_html(text: str) -> str:
    return HTML_TAG.sub("", text)


def plain_text(field: str) -> str:
    """A field as plain text on one line: no tags, no &amp; codes."""
    return " ".join(html.unescape(strip_html(field)).split())


# Cleaning up meaning fields for the hover text. The patterns fit the
# Anki-xiehanzi deck and do nothing on fields that look different:
# - headings such as "Common Meaning" (an element whose class contains
#   "title") are dropped;
# - its Definitions field has, per reading, divs with the character, pinyin,
#   zhuyin and <div class="meaning">. Only the meaning divs are kept;
# - numbers like "1." before each definition are dropped.
TITLE = re.compile(r'<(\w+)[^>]*class="[^"]*title[^"]*"[^>]*>.*?</\1>', re.S)
MEANING_DIV = re.compile(r'class="meaning">(.*?)(?:<div|</div>)', re.S)
DEF_NUMBER = re.compile(r'<span class="def-num">.*?</span>', re.S)
LINE_BREAK = re.compile(r"<br\s*/?>|</div>|</p>|</li>", re.I)


def meaning_text(field: str, limit: int = 120) -> str:
    """A meaning field as short plain text, e.g. "to learn; to study"."""
    field = "<br>".join(MEANING_DIV.findall(field)) or field
    field = DEF_NUMBER.sub("", TITLE.sub("", field))
    text = plain_text(LINE_BREAK.sub(";", field))
    # Line breaks became ";": tidy up empty and doubled separators.
    text = "; ".join(part.strip() for part in text.split(";") if part.strip())
    if len(text) > limit:
        text = text[: limit - 1].rstrip(" ;,") + "…"
    return text


class Word(NamedTuple):
    """A word from the deck, as shown when hovering a character."""

    text: str  # e.g. 学生
    pinyin: str  # e.g. xué sheng ("" if there's no pinyin field)
    meaning: str  # e.g. student ("" if there's no meaning field)


class Tile(NamedTuple):
    """One character in the grid."""

    char: str
    status: int  # UNSEEN, LEARNING, YOUNG, MATURE or MASTERED
    # Shown when hovering: the character's own note if the deck has one
    # (学 on its own), otherwise the lowest-level word containing it.
    # None if no word in the chosen decks contains the character.
    word: Word | None
    # The lowest-level word containing the character ("" if none). With
    # levels from the deck, this is the word that set the level.
    level_word: str


# How well a character is known. A character takes the *best* status among
# all the cards whose word contains it.
UNSEEN = 0  # never answered (new cards, or none)
LEARNING = 1  # in (re)learning steps, or answered but never graduated
YOUNG = 2  # in review, interval below mature_days
MATURE = 3  # in review, interval of mature_days or more
MASTERED = 4  # interval of mastered_days or more, and MASTERED_REVIEWS
#               reviews in a row answered correctly

# Successful reviews in a row (since the last time you forgot the card)
# needed for MASTERED. A long interval alone isn't enough: one review done
# very late can give a card a 100+ day interval after only 2 or 3 answers.
MASTERED_REVIEWS = 3

# Anki's card "type" column: 0 new, 1 learning, 2 review, 3 relearning.
CARD_NEW, CARD_LEARN, CARD_REVIEW, CARD_RELEARN = 0, 1, 2, 3
# Anki's card "queue" column for suspended cards.
QUEUE_SUSPENDED = -1

# Anki's review log "type" column. LOG_MANUAL is "Set due date", "Forget"
# and similar: the interval changed without you answering the card.
# LOG_FILTERED is an answer in a filtered deck that doesn't reschedule.
LOG_LEARN, LOG_REVIEW, LOG_RELEARN, LOG_FILTERED, LOG_MANUAL, LOG_RESCHEDULED = range(6)


class History(NamedTuple):
    """What a card's review log says about how well you know it."""

    answered: bool  # answered at least once (learning, review or relearning)
    interval: int | None  # interval set by the last answer (or FSRS
    #                       rescheduling); < 0 means seconds, i.e. still in
    #                       learning steps; None if there's none
    streak: int  # reviews in a row answered correctly (Hard, Good or Easy)


def read_history(rows) -> History:
    """Summarise one card's review log rows (type, ease, ivl), oldest first.

    Manual changes ("Set due date") are skipped, so pushing a card 180 days
    ahead doesn't make it mature. "Forget" (a manual change to interval 0)
    starts the card over.
    """
    answered, interval, streak = False, None, 0
    for log_type, ease, ivl in rows:
        if log_type == LOG_MANUAL:
            if ivl == 0:
                answered, interval, streak = False, None, 0
            continue
        if log_type in (LOG_LEARN, LOG_REVIEW, LOG_RELEARN):
            answered = True
        if log_type in (LOG_LEARN, LOG_REVIEW, LOG_RELEARN, LOG_RESCHEDULED):
            interval = ivl
        if log_type == LOG_REVIEW:
            streak = streak + 1 if ease > 1 else 0
    return History(answered, interval, streak)


def card_status(
    card_type: int,
    interval: int,
    history: History | None,
    mature_days: int,
    mastered_days: int,
) -> int:
    """How well one card is known.

    The interval decides young / mature / mastered, as in Anki's own stats,
    but it's taken from your answers (the review log), not only from the
    card: a card moved ahead with "Set due date" keeps the interval your
    last answer gave it. `history` None means the card has no review log at
    all (e.g. it was deleted); then the card's interval and nothing else is
    used, and it can't become MASTERED.
    """
    if card_type == CARD_NEW:
        return UNSEEN
    if card_type in (CARD_LEARN, CARD_RELEARN):
        return LEARNING
    streak = 0
    if history is not None:
        if not history.answered:
            return UNSEEN  # put into review by hand, never answered
        if history.interval is None or history.interval <= 0:
            return LEARNING  # answered in learning, then moved by hand
        interval = min(interval, history.interval)
        streak = history.streak
    if interval >= max(mastered_days, mature_days) and streak >= MASTERED_REVIEWS:
        return MASTERED
    return MATURE if interval >= mature_days else YOUNG


# The official HSK 3.1 (2025 syllabus) character lists, one file per level.
LEVEL_FILES = [
    ("level1.txt", 1, "HSK 1"),
    ("level2.txt", 2, "HSK 2"),
    ("level3.txt", 3, "HSK 3"),
    ("level4.txt", 4, "HSK 4"),
    ("level5.txt", 5, "HSK 5"),
    ("level6.txt", 6, "HSK 6"),
    ("level7-9.txt", 7, "HSK 7–9"),
]


def load_level_lists(folder: str) -> dict[str, tuple[int, str]]:
    """Read the level files into {char: (level number, label)}.

    The files are sorted by Unicode code point, not by frequency, so we only
    take the level from them; the grid order comes from the deck.
    """
    levels = {}
    for filename, level, label in LEVEL_FILES:
        with open(os.path.join(folder, filename), encoding="utf-8") as file:
            for char in HANZI.findall(file.read()):
                levels.setdefault(char, (level, label))
    return levels


def deck_filter(col, decks: list[str]) -> str:
    """SQL condition that keeps only cards in `decks` and their subdecks.

    Returns "" (no filter) when `decks` is empty. A card that's temporarily
    in a filtered deck (for example a custom study session) keeps its home
    deck in the `odid` column, so we check both columns.
    """
    if not decks:
        return ""
    deck_ids = set()
    for name in decks:
        deck_id = col.decks.id_for_name(name)
        if deck_id is None:
            raise ValueError(f'There is no deck called "{name}". Check the Hanzi Grid settings.')
        deck_ids.update(col.decks.deck_and_child_ids(deck_id))
    ids = ",".join(str(d) for d in deck_ids)
    return f"where (did in ({ids}) or odid in ({ids}))"


def collect(
    col,
    hanzi_fields: list[str],
    level_field: str,
    mature_days: int,
    decks: list[str] | None = None,
    mastered_days: int = 90,
    official_levels: dict[str, tuple[int, str]] | None = None,
    pinyin_field: str = "",
    meaning_fields: list[str] | None = None,
):
    """Return (groups, char_cards).

    Where levels come from:
      - official_levels given (from load_level_lists): each character's
        level comes from the official list. Characters on the list that
        aren't in the deck are shown too (never studied).
      - official_levels None: a character's level is the lowest level of
        any word in the deck that contains it.

    groups: [(label, [Tile, ...]), ...]
        HSK levels in order, then "Other" for studied characters with no
        level. See Tile for what each character carries.
    char_cards: {char: [card id, ...]}
        One card per word containing the character, for the previewer: the
        character's own word first (学 for 学), then by level, then in deck
        order.
    """

    # 1. Read the cards (only those in `decks`) and keep each note's best
    #    status. A note can have several cards (e.g. recognition + writing).
    #    Also remember one card per note to preview: its first card type
    #    (lowest `ord`), which is usually the "recognition" card.
    #    Suspended cards are skipped: you've chosen not to study them (for
    #    example a card with a mistake), so they don't colour a character.
    #    Review cards also need their review log (see card_status).
    card_filter = deck_filter(col, decks or [])
    card_filter += f" {'and' if card_filter else 'where'} queue != {QUEUE_SUSPENDED}"
    logs = {}  # card id -> [(type, ease, ivl), ...], oldest first
    query = (
        "select cid, type, ease, ivl from revlog where cid in "
        f"(select id from cards {card_filter} and type = {CARD_REVIEW}) "
        "order by cid, id"
    )
    for card_id, log_type, ease, ivl in col.db.execute(query):
        logs.setdefault(card_id, []).append((log_type, ease, ivl))

    note_status = {}  # note id -> best status among its cards
    note_card = {}  # note id -> (ord, card id) of the card to preview
    query = f"select id, nid, ord, type, ivl from cards {card_filter}"
    for card_id, note_id, card_ord, card_type, interval in col.db.execute(query):
        history = read_history(logs[card_id]) if card_id in logs else None
        status = card_status(card_type, interval, history, mature_days, mastered_days)
        note_status[note_id] = max(note_status.get(note_id, UNSEEN), status)
        note_card[note_id] = min(note_card.get(note_id, (card_ord, card_id)), (card_ord, card_id))

    # 2. For each note type, find the position of the word field(s), the
    #    level field, the pinyin field and the meaning field(s). Notes store
    #    all their fields in one string, separated by the character \x1f,
    #    so we need positions, not names.
    def position(names, field):
        return names.index(field) if field in names else None

    positions = {}  # note type id -> (word, level, pinyin, meaning positions)
    for notetype in col.models.all():
        names = [field["name"] for field in notetype["flds"]]
        word_pos = [names.index(n) for n in hanzi_fields if n in names]
        if word_pos:
            positions[notetype["id"]] = (
                word_pos,
                position(names, level_field),
                position(names, pinyin_field),
                [names.index(n) for n in meaning_fields or [] if n in names],
            )

    # 3. Read the notes straight from the database (much faster than loading
    #    10,000 Note objects), skipping notes with no card in the deck. For
    #    each character, keep its best status, the lowest HSK level of any
    #    word it appears in, and that word.
    char_status = {}  # character -> best status
    char_level = {}  # character -> (level number, label like "HSK 3", Word)
    first_word = {}  # character -> first Word it appeared in (for "Other")
    own_word = {}  # character -> its own note's Word (学 for 学), if any
    char_cards = {}  # character -> [(sort key, card id), ...]
    rows = col.db.execute("select id, mid, flds from notes order by id")
    for position, (note_id, notetype_id, fields) in enumerate(rows):
        if note_id not in note_status or notetype_id not in positions:
            continue
        word_pos, level_pos, pinyin_pos, meaning_pos = positions[notetype_id]
        values = fields.split("\x1f")
        text = plain_text(values[word_pos[0]])
        pinyin = plain_text(values[pinyin_pos]) if pinyin_pos is not None else ""
        # The first meaning field that isn't empty (the deck's short
        # meaning, else its full definitions).
        meanings = (meaning_text(values[pos]) for pos in meaning_pos)
        word = Word(text, pinyin, next((m for m in meanings if m), ""))

        # The note's level, e.g. "HSK 7+" -> 7. None if there's no number.
        level, label = None, ""
        if level_pos is not None:
            label = strip_html(values[level_pos]).strip()
            number = re.search(r"\d+", label)
            if number:
                level = int(number.group())

        chars = set()
        for pos in word_pos:
            chars.update(HANZI.findall(strip_html(values[pos])))
        for char in chars:
            char_status[char] = max(char_status.get(char, UNSEEN), note_status[note_id])
            first_word.setdefault(char, word)  # dicts keep insertion order
            if text == char:
                own_word.setdefault(char, word)
            if level is not None:
                if char not in char_level or level < char_level[char][0]:
                    char_level[char] = (level, label, word)
            sort_key = (text != char, level if level is not None else 99, position)
            char_cards.setdefault(char, []).append((sort_key, note_card[note_id][1]))

    # 4. Choose the level of each character: from the official list, or
    #    from the deck's words (step 3).
    if official_levels is not None:
        levels = official_levels
    else:
        levels = {char: (level, label) for char, (level, label, _) in char_level.items()}

    # 5. Put characters into groups, in the order they first appear in the
    #    deck (the xiehanzi deck is sorted by frequency), then any official
    #    characters the deck doesn't have. Characters with no level only go
    #    into "Other" if you have actually studied them.
    in_order = list(first_word) + [c for c in levels if c not in first_word]
    groups = {}  # level number -> (label, [tiles])
    other = []
    for char in in_order:
        status = char_status.get(char, UNSEEN)
        lowest = char_level[char][2] if char in char_level else first_word.get(char)
        tile = Tile(char, status, own_word.get(char) or lowest, lowest.text if lowest else "")
        if char in levels:
            level, label = levels[char]
            groups.setdefault(level, (label, []))[1].append(tile)
        elif status > UNSEEN:
            other.append(tile)

    result = [groups[level] for level in sorted(groups)]
    if other:
        result.append(("Other", other))
    cards = {char: [cid for _, cid in sorted(items)] for char, items in char_cards.items()}
    return result, cards
