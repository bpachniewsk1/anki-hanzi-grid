# Changelog

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
