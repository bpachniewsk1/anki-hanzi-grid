The easiest way to change these is the **⚙ Settings** button in the grid (the Config button in Tools → Add-ons opens the same window). The keys:

- **decks**: names of the decks to count, as shown in the deck list, for example `["Anki xiehanzi"]`. Subdecks are included. `[]` counts every deck. Default: `["Anki xiehanzi"]`.
- **levels**: where each character's HSK level comes from. `"hsk3.1"`: the official HSK 3.1 character list (2025 syllabus) bundled with the add-on. `"deck"`: the lowest HSK level of any word in the chosen decks that contains the character (uses **level_field**). Default: `"hsk3.1"`.
- **view**: which view opens: `"chars"` (characters), `"words"`, `"measure"` (measure words), `"grammar"` or `"reading"`. The View buttons in the grid change it. Default: `"chars"`.
- **measure_by**: how the Measure words view groups: `"classifier"` (measure word, then level) or `"level"`. Default: `"classifier"`.
- **hanzi_fields**: names of the fields that hold the Chinese word. Every note type that has one of these fields is scanned. Default: `["Simplified"]`.
- **level_field**: name of the field that holds the HSK level (for example `HSK 3`). Only used with `"levels": "deck"`. Default: `"HskLevel"`.
- **pinyin_field**: name of the field with the pinyin, shown when hovering a character. `""` for none. Default: `"Pinyin"`.
- **meaning_fields**: names of the fields with the meaning, shown when hovering a character. The first one that isn't empty is used. `[]` for none. Default: `["SimpleMeaning", "Definitions"]`.
- **mature_days**: a card's interval (in days) from which it counts as "mature". Default: `21`, the same as Anki's own stats.
- **well_known_days**: a card's interval (in days) from which it counts as "well known", between mature and mastered, if its last 2 reviews were also answered correctly. Kept between **mature_days** and **mastered_days**. Default: `45`.
- **mastered_days**: a card's interval (in days) from which it counts as "mastered", the top level, if its last 3 reviews were also answered correctly. Can't be lower than **mature_days**. Default: `90` (about three months).
- **weak_lapses**: how often you must have forgotten a card (Anki's lapses count) for it to get a red "weak" dot. Default: `3`.
- **deck_widget**: `true` shows a small progress summary (one bar per level) under the deck list on Anki's main screen, with an Open link. Default: `true`.
- **theme**: the look of the grid: `"modern"` (softer, rounder, greens), `"seal"` (classic with ink blue for well known and a red seal stamp for mastered), `"ink"` (ink shades, a red seal on mastered), `"clear"` (colour-blind safe) or `"classic"` (the original). The Look menu in the grid and Settings → Look change it. Default: `"modern"`.
- **font**: the font of every hanzi: `"hei"` (黑体, sans: apps and signs), `"song"` (宋体, serif: books and exam papers) or `"kai"` (楷体, brush: textbooks and handwriting). The Font switch next to Settings changes it. Default: `"hei"`.
- **font_size**: the size of every hanzi: `"s"`, `"m"` or `"l"`. The Size switch next to Settings changes it. Default: `"m"`.

Changes apply the next time the grid opens.
