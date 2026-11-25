# Stungeon – German Dungeon question banks (A1 and B1)

Source material: *Das Leben A1*, Einheiten 1–16, and *Das Leben B1*, Einheiten 1–3 (developer materials), plus the class Vokabeln lists.

## One bank per level

Each level of a dungeon has its own file here, listed in `data/dungeons.json`:

| Level | File | State |
|---|---|---|
| A1 | `questions_german_a1.json` | 3,943 questions (see "The A1 bank" below) |
| A2 | `questions_german_a2.json` | Empty, to be filled |
| B1 | `questions_german_b1.json` | 1,082 questions (below) |

A new bank uses the same question format as B1, with `"level"` set to its own level. A level stays locked in the menu until its file has questions (`systems/dungeons.is_playable`). A test checks that every question's `subject` and `level` match the file it is in.

## Files

| File | What it is |
|---|---|
| `questions_german_b1.json` | The question bank the game loads |
| `questions_german_b1_review.csv` | The same questions as a spreadsheet for checking (columns for "ok?" and notes) |
| `questions_german_a1.json`, `questions_german_a1_review.csv` | The same two files for A1 |
| `build/vocab.py` | All vocabulary: article, plural, English, Vietnamese, source |
| `build/grammar.py` | Handwritten grammar questions for each Einheit |
| `build/vocab_a1.py`, `build/grammar_a1.py` | The same two files for A1 |
| `build/build.py` | Generates the JSON and CSV of each level: `python build.py` (all) or `python build.py a1` |
| `build/extract_a1_pdf.py` | One-off helper that read the A1 Vokabeln PDFs (needs `pip install pymupdf`) |

To change or add questions, edit the vocab or grammar file of the level, then run `python build.py`. Don't edit the JSON by hand, because the next build overwrites it.

## What's inside the B1 bank

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

## The A1 bank

3,943 questions from *Das Leben A1*, Einheiten 1–16, made the same way as B1:

- **Vocabulary:** 883 words from the class Vokabeln lists (A1.zip). Unit 0, the first pages of the book, is counted as Einheit 1. Each word gets the same questions as in B1: German→English, English→German, typed, its article and its plural.
- **Grammar:** 153 questions written for the game from the "Wörter, Wendungen und Strukturen" box on each "Fit für Einheit …?" page. They are not copied exercises.
- **Topics:** `vocabulary`, `articles`, `plurals`, plus 18 grammar topics: `pronomen`, `verben_praesens`, `w_fragen`, `zahlen_uhrzeit`, `zeitangaben`, `artikel_kein_nicht`, `akkusativ`, `welch_dieser`, `adjektive`, `adverbien`, `trennbare_verben`, `modalverben`, `perfekt`, `praeteritum_sein_haben`, `praepositionen`, `possessivartikel`, `wortbildung`, `imperativ`. Small rules were merged into bigger topics (each has 4–14 questions), because the engine picks a topic first. A topic with one question would repeat it again and again.
- **Floors:** A1 has 16 Einheiten but the dungeon has 3 floors. The bank's `"floor_einheiten": {"1": 5, "2": 10, "3": 16}` says floor 1 asks Einheiten 1–5, floor 2 asks 1–10 and floor 3 asks 1–16. A bank without it (B1) uses Einheiten 1 to n on floor n.

What was fixed in the Vokabeln lists:

- **Cut-off words** completed, where the PDF cell was too narrow: Automobilkaufmann, Automobilkauffrau, Informatikkaufmann, Wohngemeinschaft, Überschwemmung, Frühstück machen.
- **Wrong plurals** fixed or removed: der Sport (not "Sportarten"), die Musik, die Schokolade, der Kaffee and der Käse get no plural question; Laptops, Werkstätten, Knie, Öfen, Vorschläge, Schwäger, Mottos. Uncountable words (Wetter, Schnee, Gemüse, Glück, …) get no plural question.
- **Plural-only nouns** (die Eltern, Geschwister, Großeltern, Leute, Ferien, Senioren, Lebensmittel, Pommes) get no article or plural question.
- **Old spellings:** Erdnuss, Schluss, nass (not ß).
- **English typos and unclear meanings** fixed, for example grez → grey, stzle → style, potatoe → potato, maritial status → marital status, philharmony → philharmonic orchestra, ordnen "to order" → "to sort, to arrange", Ausverkauft → der Ausverkauf (clearance sale). `vocab_a1.py` already holds the fixed words, so edit that file from now on.
- **Repeats removed:** a word listed in several Einheiten is kept only the first time.
- **Typed questions** are skipped when two German words share the same English meaning (to know = kennen or wissen), so a typed answer always has one right word.

Still to do:

- **Vietnamese:** only about 40% of the A1 words have `meaning_vi` (the lists are empty for the rest).
- **Bosses:** the bosses in `data/enemies.json` ask B1 grammar topics. In A1 those topics don't exist, so they ask any topic. Owner D can give A1 its own boss topics later.
- **Please have a German speaker check** a sample of `questions_german_a1_review.csv`, especially the grammar questions.

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
