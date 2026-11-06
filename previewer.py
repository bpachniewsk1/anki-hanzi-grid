# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Card preview window for Hanzi Grid.

Instead of building a preview window ourselves, we reuse Anki's own: the
same one the Browser opens with its "Preview" button. Anki's
`MultiCardPreviewer` already draws the card (with your card template and
styling), plays audio, and has < and > buttons. A subclass only has to say
*which* card to show and how to move between cards.

Methods starting with an underscore (`_on_next_card` …) are Anki internals,
not an official add-on API, so a future Anki version could rename them.
Checked against Anki 24.06 to 25.09.
"""

from __future__ import annotations

from aqt import mw
from aqt.browser.previewer import MultiCardPreviewer


class CharPreviewer(MultiCardPreviewer):
    """Shows every word containing one character, one card at a time, on
    the answer side (back of the card).

    > (or Right arrow) goes to the next word, < (or Left arrow) back.
    """

    def __init__(self, char: str, card_ids: list[int], on_close) -> None:
        super().__init__(parent=None, mw=mw, on_close=on_close)
        self.char = char
        self.card_ids = card_ids
        self.index = 0  # which card in card_ids is showing
        self.last_shown = None

    # --- The two methods every previewer must have -------------------------

    def card(self):
        return mw.col.get_card(self.card_ids[self.index])

    def card_changed(self) -> bool:
        # Anki asks this before drawing. Answering True ("new card") makes
        # Anki start on the question side. Instead, when the card is new we
        # switch to the answer side ourselves and answer False, so Anki
        # keeps it. (_state is "question" or "answer", Anki's own variable.)
        current = self.card_ids[self.index]
        if current != self.last_shown:
            self.last_shown = current
            self._state = "answer"
        return False

    # --- Moving between cards ----------------------------------------------
    # Anki's < and > first flip between question and answer. We always show
    # the answer, so they go straight to the previous / next word.

    def _on_prev(self) -> None:
        self._on_prev_card()

    def _on_next(self) -> None:
        self._on_next_card()

    def _on_prev_card(self) -> None:
        if self.index > 0:
            self.index -= 1
            self.show_current()

    def _on_next_card(self) -> None:
        if self.index < len(self.card_ids) - 1:
            self.index += 1
            self.show_current()

    def show_current(self) -> None:
        self.update_title()
        self.render_card()

    def _should_enable_prev(self) -> bool:
        return self.index > 0

    def _should_enable_next(self) -> bool:
        return self.index < len(self.card_ids) - 1

    def _render_scheduled(self) -> None:
        # After each redraw, grey out < or > at the ends of the list.
        super()._render_scheduled()
        self._updateButtons()

    # --- Window title --------------------------------------------------------

    def _create_gui(self) -> None:
        super()._create_gui()
        self.update_title()

    def update_title(self) -> None:
        self.setWindowTitle(
            f"{self.char}: word {self.index + 1} of {len(self.card_ids)}"
        )
