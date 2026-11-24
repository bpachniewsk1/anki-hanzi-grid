# Changelog

## 1.9.0 (2026-11-24)

- Two new looks: **Gems** (peach, sky, blue, violet for well known, gold
  for mastered) and **Seal** (rice paper, pale jade, jade, ink blue for
  well known, a red seal stamp 印章 for mastered). Modern stays the
  default; Classic is still there.
- A **Look** menu at the top right of the grid switches instantly, without
  rebuilding, and remembers the choice (config key `theme`).

## 1.8.0 (2026-11-24)

- **Well known**, a new level between mature and mastered: a 45+ day
  interval and the last 2 reviews answered correctly. Deep teal tiles with
  a gold line along the bottom, on the way to mastered's gold characters.
  Shown in the legend, the progress bars and numbers ("N well known"), the
  deck-list summary, the Mature+ filter and the Reading view. The number
  of days is a new setting, Well known from (`well_known_days`).

## 1.7.1 (2026-11-19)

- Find works much more visibly in every view: matches get a yellow ring
  (the current one blue and slightly larger), levels and grammar bands
  without a match are hidden, the Next up rows step aside, the page
  scrolls to the first match, and a counter shows "3 / 52". Enter and
  Shift+Enter step through the matches, Esc clears the search.

## 1.7.0 (2026-11-18)

- **Grammar checklist**: a checkbox on every grammar point to tick once
  you've mastered it. "N / M mastered" with a bar for all levels and for
  each level, updated as you tick; Show → To do / Mastered filters the
  list. The ticks are saved in your collection's settings (key
  `hanziGridGrammarDone`), so they sync with AnkiWeb and survive
  reinstalling the add-on.

## 1.6.0 (2026-11-17)

- **Reading view**: paste any Chinese text. The words are matched against
  your decks (longest match first), every character is coloured by its
  status, the line above the text says how much of it you have studied,
  and the words you haven't studied are listed by level with how often
  they occur. Hover for pinyin and meaning, click to preview the card.
  Characters in none of your decks get a dotted red underline. The text
  is kept between openings. A Sample text button shows how it works.
- Fix: the page script stopped early in views without a Find box.

## 1.5.0 (2026-11-16)

- **Modern look** (default): flat rounded tiles, borderless buttons and
  cards, a fresher green scale (amber → mint → emerald → deep green with
  gold), the same in the deck-list summary. The original look is still
  there as **Classic**: Settings → Look (config key `theme`).

## 1.4.1 (2026-11-16)

- Measure words view: Find now searches by measure word, pinyin or gloss
  (本, ben, books) and shows the whole block, or by word and hides the
  rows and blocks with no match. Clearer layout: tinted headings, one row
  per HSK level. The note explains that a word with several measure words
  (狗: 只 or 条) appears under each.

## 1.4.0 (2026-11-16)

- **Measure words view**: words grouped by the classifier they take
  (本 → 书, 课本, 杂志 …), by HSK level inside, each measure word with
  its own tile, pinyin, gloss and progress bar; 个 last and collapsed.
  "Group by" switches to level first (config key `measure_by`). Data for
  1,452 words from CC-CEDICT (CC BY-SA 4.0) in `data/classifiers/`.
- Hover boxes in the Words view and the character page now show a word's
  measure word(s).

## 1.3.1 (2026-11-16)

- Grammar view: every one of the 496 grammar points now has a note with a
  pattern, an explanation and example sentences with pinyin (354 added).

## 1.3.0 (2026-11-16)

- **Grammar view**: the grammar points of each level, from the Chinese
  Grammar Wiki (495 points, with links), about 140 of them with a short
  note, pattern and example sentences with pinyin, including 过, 着, the
  three de (的, 得, 地), 了, 把, 被 and the complements. The tile next to
  each point shows how well you know its key character or word; Find
  searches the points. Data in `data/grammar/`.
- **Summary on the deck list**: one bar per level under Anki's deck list
  with "+N this week" and an Open link. Built in the background and cached,
  so the deck list stays fast. "Show a progress summary on the deck list"
  in Settings (config key `deck_widget`) turns it off.

## 1.2.0 (2026-11-16)

- **Words view**: one tile per word, grouped by the words' HSK levels,
  with the same colours, progress bars and hover boxes. Switch with the
  View buttons (config key `view`).
- **Character page**: clicking a character now opens a page with every
  word that contains it, grouped by level and coloured by status, with a
  progress bar, "Open all cards" and "Find in Browser". Click a word to
  preview its card.
- **"+N this week"** in the progress lines: characters or words first
  answered in the last 7 days.
- **Next up** under each level: the first unstudied characters or words,
  in deck order.
- **Weak marks**: a red dot on tiles forgotten 3 or more times ("Weak
  from" in Settings, config key `weak_lapses`); the hover box says how
  often.
- **Show** filter (not studied, in progress, mature+, weak) and a **Find**
  box.
- Shift+click a word to find it in the Browser.

## 1.1.2 (2026-11-08)

- Repackaged: an early 1.1.1 package on AnkiWeb was missing the change
  that ignores suspended cards. No other changes.

## 1.1.1 (2026-11-08)

- Fix: cards moved with **Set due date** were shown as mature or mastered
  without being reviewed. Statuses now use the interval your last answer
  gave a card (from the review log); manual changes are ignored. A card put
  into review that way without being answered counts as not studied.
- Mastered now also needs the last 3 reviews answered correctly (since the
  last time the card was forgotten), so one late review can't make a card
  mastered after only 2 or 3 answers.
- Suspended cards are ignored, so suspending a card (for example one with
  a mistake) stops it colouring its characters or showing in the preview.

## 1.1.0 (2026-11-07)

- New top status **mastered**: cards with an interval of 90 days or more
  (gold characters on deep green). Change it with "Mastered from" in the
  Settings window (config key `mastered_days`).
- Progress lines now also count mastered characters.

## 1.0.0 (2026-11-06)

First release.

- Grid of every character in the chosen decks, grouped by HSK level and
  coloured by card status (not studied, learning, young, mature).
- Progress bar for each level and for all levels.
- Levels from the official HSK 3.1 character list (2025 syllabus), or
  worked out from the decks' word levels.
- Hover a character to see its pinyin and meaning.
- Click a character to see the answer side of the cards of every word
  containing it; Shift+click to open the Browser.
- Settings window: decks, level source, word field, HSK level field,
  pinyin and meaning fields, mature threshold.
