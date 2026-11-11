# Stungeon features: what is in, what is next, what waits

Written on 11 Nov 2026 from the 37 design answers (the chat with Claude) and docs/HANDOFF.md.
Scope for now is the **German Dungeon** only. Feature freeze is 22 Nov, the exhibit is 28 Nov.

How to read the status:

- **Done**: built and tested.
- **Hook ready**: the game already calls a function at the right moment and hands it the data.
  The function is a placeholder; its owner writes the rule inside it. Nothing else has to change.
- **Now**: worth doing before the freeze.
- **Later**: saved for after the exhibit.

Owners: A world, B combat and UI, C AI and questions, D systems and content (see the Team Guides).

## 1. Now: the list to finish before 22 Nov

In the order that matters most for the exhibit.

| # | Feature | Owner | What is ready | What is missing |
|---|---|---|---|---|
| 1 | Knowledge tracing (BKT) per topic | C | The Progress screen (M) shows mastery per topic; the engine calls `tracker.update()` after every answer | `KnowledgeTracker.update()` in `ai/mastery.py` (every topic shows 50% until then) |
| 2 | Pick the topic first, weighted by low mastery | C | `QuestionEngine._choose()` receives the pool, the enemy's topics and the "weakest" flag | The body of `_choose()` (now random, so grammar almost never appears) |
| 3 | Damage formula | B | `combat/damage.py` is called for every hit | The formula: ultimate bonus, weapons, level |
| 4 | Faster answer = critical hit | B | `battle.seconds` holds the answer times; a timer is shown | The rule, in `effects.change_player_damage()` |
| 5 | Streak of right answers multiplies damage | B | `battle.engine.streak` counts it; "Streak x3" is shown in fights | The rule, in `effects.change_player_damage()` |
| 6 | After a miss, a chance that the enemy loses its turn | B | `effects.enemy_loses_turn()` is called before every enemy turn | The chance (a number in `data/`) |
| 7 | Balance with potion-only healing | D | All numbers are in `data/*.json` | Real numbers. Today a player who never drinks dies on floor 1 |
| 8 | Equipment that does something | D + B | Seven slots, the bag, descriptions, loot, shop | Effects: weapons multiply damage, armour reduces damage or gives time |
| 9 | 3 buffs and 4 debuffs (v1 scope) | B + D | Five hook moments in `combat/effects.py`; `engine.to_typed()` for Blind | Which ones, and their rules |
| 10 | Utility moves (War Cry, Reveal, Evasion) | B | They cost resource and call `effects.use_utility()` | What each one does |
| 11 | Adaptive enemies (3 rules + taunts) | C | `HabitTracker.record_move()` is called after every answer; `adapt()` before every enemy turn | The three rules and the taunt texts |
| 12 | A* pathfinding for chasing monsters | C | Monsters call `astar()`; until it returns a path they step straight at the player | `ai/pathfinding.py` |
| 13 | Scrolls (hint, skip) | D | Consumables work; `systems/item_effects.py` has two effects | New effect types and items |
| 14 | Questions checked by a German speaker | C + team | `questions/data/questions_german_b1_review.csv` | The check itself, and `meaning_vi` |
| 15 | Own look: font, repainted art | D | Drop-in PNG names in `assets/README.md`; themes per floor | A CC0 pixel font; our own repaints |
| 16 | Sound | D | Nothing yet | Needs CC0 sound files first; then a small loader |
| 17 | Does an item cost your turn in a fight? | B | `effects.item_costs_turn()` (placeholder: yes) | The decision |
| 18 | Elites, mini-bosses, traps, choices: real content | D | All in `data/` as placeholders: `enemies.json` (elite, miniboss), `choices.json`, `progression.json` (trap_damage) | Names, numbers, more choices |
| 19 | Room kinds and their weights | A | `dungeon/floor.py`: start, boss, treasure, trap, den, normal; cut corners | Tuning, more kinds |

## 2. All 37 answers

### Combat

| # | Answer | Status | Notes |
|---|---|---|---|
| 1 | Turn-based, question pops up, time pauses | Done | Monsters on the map stop while a fight is open |
| 2 | Timer; faster answer = more critical | Hook ready (B) | See Now 4. There is no time LIMIT yet: a limit and what happens when it runs out are B's decision |
| 3 | Multiple choice, tick-all and typed answers | Done | Typed answers accept ae/oe/ue/ss. "More time for typed" needs the time limit first |
| 4 | Wrong answer = miss and lose the turn; chance that the enemy loses its turn | Done + hook ready (B) | Miss and lost turn are done. See Now 6 |
| 5 | Streak multiplies damage | Hook ready (B) | See Now 5 |

### Character and progression

| # | Answer | Status | Notes |
|---|---|---|---|
| 6 | Classes | Done | Warrior, Mage, Archer. Races and designing your own character: Later |
| 7 | Skill points on level up | Later | Now: a level up raises max HP and unlocks moves |
| 8 | Skill tree per class and race | Later | |
| 9 | Weapon mastery, hidden class dungeons, level gates on floors | Later | |

### Weapons, armour and loot

| # | Answer | Status | Notes |
|---|---|---|---|
| 10 | Weapons as damage multipliers with effects and looks | Looks done, effects Now (D + B) | The equipped weapon is held and swung. See Now 8 |
| 11 | Armour reduces damage or gives time; special skills on high tiers | Slots done, effects Now (D + B) | Head, body, legs, shoes, two accessories. See Now 8 |
| 12 | Rarity tiers; loot from monsters, bosses and chests | Done | Common to Legendary. Mythical: Later. End-of-floor reward chest: Later |
| 13 | Gold, shop between floors; selling; wandering traders | Buying done | Selling has its rule (`shop.sell`) but no screen yet: small, could be Now. Traders: Later |
| 14 | HP potions, buff potions, hint and skip scrolls, gamble scroll | Potions done | Potions can be used in a fight (I). Scrolls: Now 13. Buff potions need buffs (Now 9). Gamble scroll: Later |

### Buffs and debuffs

| # | Answer | Status | Notes |
|---|---|---|---|
| 15 | Eight buffs | Hook ready (B + D) | v1 scope is 3 of them. See Now 9 |
| 16 | Confusion, Silence, Blind, Haste | Hook ready (B + D) | Blind (multiple choice becomes typed) has its helper already |
| 17 | Enemies cast debuffs tied to their topic | Later | Needs debuffs first |

### Enemies and bosses

| # | Answer | Status | Notes |
|---|---|---|---|
| 18 | Enemy types for the German Dungeon | Placeholder (D) | 4 enemies and 3 bosses exist as placeholders |
| 19 | Boss = summary of the chapter, question chains, phases | One boss per floor done | Bosses ask their own topic list. Chains use the ultimate's 3 questions. Phases: Later |
| 20 | Boss difficulty fixed | Done | |
| 21 | Bosses a bit harder in later runs; NG+ | Later | |

### Dungeon structure

| # | Answer | Status | Notes |
|---|---|---|---|
| 22 | Random floors each run | Done | Room kinds (treasure, trap, den), cut corners, chests, chasing monsters, elites, a mini-boss, fog of war, a minimap, a random theme per run |
| 23 | One floor per Einheit, cumulative | Done | 3 floors for Einheiten 1 to 3 |
| 24 | Roguelike (permadeath) and Checkpoint modes | Checkpoint done | Saved when a floor starts. Roguelike: Later |
| 25 | Secret rooms; chests that need a hard question | Chests done | Plain chests, and a treasure room guarded by a mini-boss. A question to open them, and secret rooms: Later |

### Making it addictive

| # | Answer | Status | Notes |
|---|---|---|---|
| 26 | Daily challenge and streak rewards | Later | |
| 27 | Achievements and titles with buffs | Later | |
| 28 | Review room for questions you got wrong | Later | The end screen already lists your weakest topics |
| 29 | Cosmetics | Later | |
| 30 | Local leaderboards | Later | |

### Learning features

| # | Answer | Status | Notes |
|---|---|---|---|
| 31 | Show the right answer and an explanation; vary questions so they can't be memorised | Explanation done | Answer order is shuffled every time. Varying the questions themselves: Later |
| 32 | See mastery, level and XP during the run | Done | Press M, or Esc and "Progress". Mastery needs Now 1 to move |
| 33 | My Materials mode | Later | |

### Look and feel

| # | Answer | Status | Notes |
|---|---|---|---|
| 34 | Pixel art | Done | Three CC0 packs, credited in assets/CREDITS.md. See Now 15 |
| 35 | Music and sound | Now 16, if files are found | |
| 36 | English, German or Vietnamese UI | English done | All text is in `core/strings_en.json`, so another language is one more file. Later |
| 37 | Name: Stungeon | Done | |

## 3. Later: the saved list

Kept from the design chat so nothing is lost. None of these is needed for the exhibit.

- **Character:** races, designing your own character, skill points, skill trees, weapon mastery.
- **World:** hidden class dungeons with unique rewards, level gates on floors, secret rooms, question chests,
  end-of-floor reward chests, wandering traders, doors, keys, fountains.
- **Combat:** multi-phase bosses, bosses that learn across runs, NG+, topic debuffs cast by enemies,
  gamble scroll, item slots in the hotbar.
- **Modes:** Roguelike (permadeath), review room, daily challenge.
- **Rewards:** achievements, titles with buffs, cosmetics, Mythical items, leaderboards.
- **Learning:** question variation, My Materials uploads, other subjects.
- **Look:** Vietnamese and German UI, attack animations drawn by us, armour art (none of the three packs has any).

## 4. Added after the design chat (11 Nov 2026)

These were not in the 37 answers. They were added because dungeon crawlers usually have them.

| Feature | Status | Notes |
|---|---|---|
| Fog of war | Done | A room is shown when you enter it; corridors show a few cells around you |
| Minimap | Done | Top right; shows explored cells, chests, monsters you have seen, guards in pink |
| Hit effects | Done | Screen shake, the enemy flashes white, a short pause, damage numbers |
| Room variety | Done, placeholder weights (A) | See Now 19 |
| Elite monsters | Done, placeholder numbers (D) | A gold ring on the map; stronger, better loot |
| Mini-boss | Done, placeholder content (D) | One per floor, guards the treasure room, uses the packs' big monsters |
| Spike traps | Done, placeholder damage (D) | Only in trap rooms; the middle row and column are safe |
| Choice between floors | Done, placeholder content (D) | Three of six choices; each has a risk or a reward |
| Random theme per run | Done | Each floor lists themes in `data/enemies.json`; the run's seed picks one |
| Sound, tutorial fight | Not started | Suggested for before the exhibit |
