The easiest way to change these is the **⚙ Settings** button in the grid (the Config button in Tools → Add-ons opens the same window). The keys:

- **decks**: names of the decks to count, as shown in the deck list, for example `["Anki xiehanzi"]`. Subdecks are included. `[]` counts every deck. Default: `["Anki xiehanzi"]`.
- **levels**: where each character's HSK level comes from. `"hsk3.1"`: the official HSK 3.1 character list (2025 syllabus) bundled with the add-on. `"deck"`: the lowest HSK level of any word in the chosen decks that contains the character (uses **level_field**). Default: `"hsk3.1"`.
- **view**: which view opens, `"chars"` (characters) or `"words"`. The View buttons in the grid change it. Default: `"chars"`.
- **hanzi_fields**: names of the fields that hold the Chinese word. Every note type that has one of these fields is scanned. Default: `["Simplified"]`.
- **level_field**: name of the field that holds the HSK level (for example `HSK 3`). Only used with `"levels": "deck"`. Default: `"HskLevel"`.
- **pinyin_field**: name of the field with the pinyin, shown when hovering a character. `""` for none. Default: `"Pinyin"`.
- **meaning_fields**: names of the fields with the meaning, shown when hovering a character. The first one that isn't empty is used. `[]` for none. Default: `["SimpleMeaning", "Definitions"]`.
- **mature_days**: a card's interval (in days) from which it counts as "mature". Default: `21`, the same as Anki's own stats.
- **mastered_days**: a card's interval (in days) from which it counts as "mastered", the top level, if its last 3 reviews were also answered correctly. Can't be lower than **mature_days**. Default: `90` (about three months).

- **weak_lapses**: how often you must have forgotten a card (Anki's lapses count) for it to get a red "weak" dot. Default: `3`.
- **deck_widget**: `true` shows a small progress summary (one bar per level) under the deck list on Anki's main screen, with an Open link. Default: `true`.

Changes apply the next time the grid opens.
