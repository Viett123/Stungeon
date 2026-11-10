# Stungeon – German Dungeon question bank (B1, Einheiten 1–3)

Source material: *Das Leben B1*, Einheiten 1–3 (developer materials), plus the class Vokabeln lists.

## Files

| File | What it is |
|---|---|
| `questions_german_b1.json` | The question bank the game loads |
| `questions_german_b1_review.csv` | The same questions as a spreadsheet for checking (columns for "ok?" and notes) |
| `build/vocab.py` | All vocabulary: article, plural, English, Vietnamese, source |
| `build/grammar.py` | Handwritten grammar questions for each Einheit |
| `build/build.py` | Generates the JSON and CSV from the two files above |

To change or add questions, edit `vocab.py` or `grammar.py`, then run `python build.py`. Don't edit the JSON by hand, because the next build overwrites it.

## What's inside

1,082 questions in total.

| | Einheit 1 | Einheit 2 | Einheit 3 |
|---|---|---|---|
| Theme | Bildung (er)leben | Vorhang auf! | Miteinander – füreinander! |
| Vocabulary entries | 59 | 104 | 72 |
| Questions | 273 | 472 | 337 |

**Topics:**
- `vocabulary`: German→English (easy), English→German multiple choice (medium), English→German typed (hard)
- `articles`: der/die/das (medium), "select all feminine nouns" rounds (hard)
- `plurals`: typed plural forms (hard)
- Grammar, one topic per rule:
  - E1: `konjunktiv2_modalverben`, `irgend_woerter`, `ziemlich_sehr_besonders`, `um_zu`, `nomen_verb`, `abkuerzungen`
  - E2: `infinitiv_mit_zu`, `nebensatz_waehrend`, `verben_mit_praepositionen`, `passiv_praesens`, `wechselpraepositionen`, `nicht_sondern`
  - E3: `konjunktiv2_praesens`, `deshalb_darum_deswegen`, `komposita_artikel`, `passiv_praeteritum`, `diskussion_redemittel`

Each topic is a mastery category for knowledge tracing, and a natural home for a themed enemy. For example, an Article Goblin uses `articles` and a Conjunctive Wraith uses the Konjunktiv II topics.

## Question format

```json
{
  "id": "de-b1-e2-articles-004",
  "subject": "german", "level": "B1", "einheit": 2,
  "topic": "articles",
  "difficulty": "medium",
  "type": "multiple_choice",
  "question": "___ Vorhang  (curtain)",
  "choices": ["der", "die", "das"],
  "answer": "der",
  "explanation": "der Vorhang (pl. die Vorhänge) = curtain",
  "source": "vokabeln",
  "word": "der Vorhang", "meaning_en": "curtain", "meaning_vi": "rèm, màn sân khấu"
}
```

- `type`:
  - `multiple_choice`: `answer` is one string.
  - `multi_select`: `answer` is a list, and the player must pick exactly those.
  - `typed`: `answer` is a string, and `accept` lists other answers that also count.
- `difficulty` maps to damage: easy 10, medium 25, hard 50 (stored in `difficulty_damage`).
- `source`:
  - `vokabeln`: from the class list.
  - `einheit_text`: a word that appears in the textbook but is missing from the Vokabeln list.
  - `einheit_text_grammar`: a grammar question.
- `meaning_vi` is there for the Vietnamese UI. Vocabulary question text is in English for now.

## Rules the game code should follow

1. **Shuffle the answer order** every time a question is shown. Correct answers are always listed first in the file.
2. **Checking typed answers:** trim spaces and ignore upper/lower case. Count both the `answer` and anything in `accept` as correct. Optional: accept "ss" for "ß" and "ae/oe/ue" for "ä/ö/ü", since many keyboards lack umlauts.
3. **Blind debuff:** turns multiple choice into typed. Use the question's `word` as the typed answer for vocabulary questions, and for grammar questions use the correct choice.
4. **Mixing grammar and vocabulary:** grammar has far fewer questions (72 vs about 1,000). Pick a topic first, weighted by low mastery, and then a question within it. Otherwise grammar will almost never appear.
5. **Bosses and cumulative floors:** floor n draws from Einheiten 1 to n. A boss draws mostly from the player's weakest topics.

## Notes on the materials

- **There is no Vokabeln list for Einheit 1.** All Einheit 1 vocabulary was taken from the textbook pages. The Vokabeln numbering starts at 171 (plus 82–83), so rows 1–170 probably belong to Einheit 1. If you have that list, add it and mark the entries `vokabeln`.
- **Two uploaded files are identical:** "Vokabeln Einheit 2-1" and "Vokabeln Einheit 2a".
- **Duplicates removed:** Kulisse, frisieren, husten (each listed twice in E2), and Lust (in both E2 and E3, kept in E2).
- **English fixed from the Vokabeln list:**

| Word | List said | Changed to |
|---|---|---|
| irgendwo | anzwhere | somewhere, anywhere |
| streichen | to cancel, eleminate | to cut, to delete |
| sinnvoll | meaningfull | meaningful, sensible |
| erquicken | to rejoice | to refresh (literary) |
| der Irrtum | ignorance, wrong thinking | error, mistake |
| veralten | to age | to become outdated |
| der Dramaturg | director | dramaturge (der Regisseur is the director) |
| die Öffentlichkeit | publicity | the public |
| sich beteiligen | to chip in | to take part |
| der Beleuchter | lighter | lighting technician |
| der Bürger | civilian | citizen |
| die Feuerwehr | fire fighter | fire brigade |
| der Autokorso | parade | celebratory car parade |

- **No plural questions** for words that are uncountable or rarely plural: Lust, Publikum, Lampenfieber, Pampa, Öffentlichkeit, Jugend, Zukunft, Glück, Abitur, Verhalten, Naturschutz, Naturschutzbund, Umwelt, Schutz.
- **Please have a German speaker check** the `meaning_vi` translations and a sample of the questions using the review CSV before the demo.
- **Copyright:** the questions use the textbook's vocabulary and grammar topics but are written for the game, not copied from the exercises. Keep it that way if the game is shared publicly.
