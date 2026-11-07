# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Settings window for Hanzi Grid.

Opened from the "Settings" button in the grid, or from
Tools > Add-ons > Hanzi Grid > Config. It is an ordinary Qt dialog built
from standard widgets:

    QListWidget  checkable list of decks
    QComboBox    drop-down lists
    QSpinBox     number box
    QFormLayout  lays them out as "label: widget" rows

This file only shows the settings and collects the new values. Saving them
happens in __init__.py, with Anki's add-on config API
(`mw.addonManager.writeConfig`): the same place the JSON config editor
writes to, a file called meta.json in the add-on folder.
"""

from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    Qt,
    qconnect,
)
from aqt.utils import disable_help_button

NO_FIELD = "(none)"


def selected_decks(config: dict) -> list[str]:
    """The decks to count, as a list of names. Empty list = every deck.

    Older versions stored a single deck name under "deck". Move it over to
    the new "decks" list, so old settings keep working.
    """
    if "deck" in config:
        old = config.pop("deck")
        config["decks"] = [old] if old else []
    return config.get("decks", [])


def field_name(box: QComboBox) -> str:
    """The field chosen in a drop-down, or "" for "(none)"."""
    name = box.currentText()
    return "" if name == NO_FIELD else name


class SettingsDialog(QDialog):
    def __init__(self, config: dict, levels_choices, on_save) -> None:
        super().__init__(mw)
        self.config = config
        self.on_save = on_save  # called with the new config after Save
        self.setWindowTitle("Hanzi Grid Settings")
        disable_help_button(self)
        form = QFormLayout(self)

        # --- Decks: one checkbox per deck --------------------------------
        self.deck_list = QListWidget()
        chosen = set(selected_decks(config))
        for deck in mw.col.decks.all_names_and_ids(include_filtered=False):
            item = QListWidgetItem(deck.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = deck.name in chosen
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.deck_list.addItem(item)
        self.deck_list.setMinimumHeight(220)
        form.addRow("Decks:", self.deck_list)
        hint = QLabel("Subdecks are included. Tick nothing to count every deck.")
        hint.setWordWrap(True)
        form.addRow("", hint)

        # --- Where levels come from --------------------------------------
        # addItem(text, data): the text is shown, the data is what we save.
        self.levels = QComboBox()
        for value, text in levels_choices:
            self.levels.addItem(text, value)
        self.levels.setCurrentIndex(max(0, self.levels.findData(config.get("levels"))))
        form.addRow("Levels:", self.levels)

        # --- Which fields to read ----------------------------------------
        # Offer every field name used by any note type.
        field_names = sorted(
            {field["name"] for notetype in mw.col.models.all() for field in notetype["flds"]}
        )
        self.word_field = QComboBox()
        self.word_field.addItems(field_names)
        word_fields = config.get("hanzi_fields") or ["Simplified"]
        self.word_field.setCurrentText(word_fields[0])
        form.addRow("Word field:", self.word_field)

        def optional_field(current: str) -> QComboBox:
            # A drop-down of field names, with "(none)" first.
            box = QComboBox()
            box.addItems([NO_FIELD] + field_names)
            box.setCurrentText(current or NO_FIELD)
            return box

        self.level_field = optional_field(config.get("level_field", ""))
        form.addRow("HSK level field:", self.level_field)

        # Shown when hovering a character.
        self.pinyin_field = optional_field(config.get("pinyin_field", ""))
        form.addRow("Pinyin field:", self.pinyin_field)
        meanings = (config.get("meaning_fields") or []) + ["", ""]
        self.meaning_field = optional_field(meanings[0])
        form.addRow("Meaning field:", self.meaning_field)
        self.backup_meaning_field = optional_field(meanings[1])
        form.addRow("…if that's empty:", self.backup_meaning_field)

        # --- Mature and mastered thresholds -------------------------------
        self.mature_days = QSpinBox()
        self.mature_days.setRange(1, 3650)
        self.mature_days.setSuffix(" days")
        self.mature_days.setValue(config.get("mature_days", 21))
        form.addRow("Mature from:", self.mature_days)
        self.mastered_days = QSpinBox()
        self.mastered_days.setRange(1, 3650)
        self.mastered_days.setSuffix(" days")
        self.mastered_days.setValue(config.get("mastered_days", 90))
        form.addRow("Mastered from:", self.mastered_days)

        # --- Save / Cancel -------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        qconnect(buttons.accepted, self.accept)
        qconnect(buttons.rejected, self.reject)
        form.addRow(buttons)

        self.resize(460, 630)

    def accept(self) -> None:
        """Save was clicked: copy the widgets' values into the config."""
        decks = []
        for row in range(self.deck_list.count()):
            item = self.deck_list.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                decks.append(item.text())
        self.config["decks"] = decks
        self.config["levels"] = self.levels.currentData()
        self.config["hanzi_fields"] = [self.word_field.currentText()]
        self.config["level_field"] = field_name(self.level_field)
        self.config["pinyin_field"] = field_name(self.pinyin_field)
        meanings = [field_name(self.meaning_field), field_name(self.backup_meaning_field)]
        self.config["meaning_fields"] = [name for name in meanings if name]
        self.config["mature_days"] = self.mature_days.value()
        # Mastered can't come before mature.
        self.config["mastered_days"] = max(self.mastered_days.value(), self.mature_days.value())

        super().accept()  # closes the dialog
        self.on_save(self.config)  # __init__.py saves it and rebuilds the grid
