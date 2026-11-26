# Stungeon – handoff notes (as of 9 Nov 2026)

Read this first in any new chat or Claude Code session about Stungeon.

## Where things live
- Design doc: "Stungeon – Project Overview" — https://claude.ai/artifact/KFh6efHhWKdX2pZqXmXvij
- Role guides: "Stungeon – Team Guides" (tabs: Start here, A World, B Combat and UI, C AI and questions, D Systems and content) — https://claude.ai/artifact/CWoDxFi7LUu9j99jkQdYDR
- Question bank: stungeon_german_b1.zip (questions_german_b1.json, review CSV, README, build/vocab.py, build/grammar.py, build/build.py). Goes into the repo at questions/data/ (JSON) and questions/build/ (scripts).

## Key decisions
- Educational dungeon-crawler RPG, Python 3.11 + pygame-ce, English UI only for v1 (Vietnamese/German UI later).
- Team of 4. Việt = project lead + (recommended) role C: AI and question engine.
- Deadline: version 1 shown at the exhibit on 28 Nov 2026. Feature freeze 22 Nov, build locked 26 Nov.
- German Dungeon: Das Leben B1, Einheiten 1–3 = floors 1–3, cumulative. 1,082 questions (vocabulary, articles, plurals, 17 grammar topics). Pick topic first, then question.
- Combat: turn-based. Player picks a named class move; stronger move = harder question. Tiers: Basic (easy, 10), Skill (medium, 25), Power (hard/typed, 50, lvl 3), Ultimate (3 hard questions from weakest topics, 35 each +45, lvl 5), Utility (no question, lvl 2). Wrong answer = miss, cost still spent, enemy gets its turn.
- Classes: Warrior (Rage: Slash, Shield Bash, Berserker Cleave, Titan's Wrath, War Cry), Mage (Mana: Arcane Bolt, Frost Lance, Fireball, Meteor Storm, Reveal), Archer (Focus: Quick Shot, Piercing Arrow, Poison Arrow, Arrow Rain, Evasion).
- AI parts: Bayesian Knowledge Tracing per topic, HabitTracker adaptive enemies (3 rules + taunts), A* pathfinding.
- v1 scope: 3 floors, Checkpoint mode, loot (Common–Legendary), shop between floors, potions/scrolls, 3 buffs, 4 debuffs, 1 boss per floor, save per floor, demo mode (~10 min run).
- Deferred: Roguelike mode, races, skill trees, weapon mastery, traders, gamble scroll, achievements/titles, daily challenges, cosmetics, review room, Mythical items, My Materials uploads, NG+, other subjects.
- Rule: ai/, questions/, systems/ never import pygame (keeps logic testable and portable, e.g. to Godot later).

## Updates after the handoff (11 Nov 2026)
- What is built, what is next and what waits is tracked in docs/FEATURES.md. Read it before picking a task.
- Team rule: nothing heals the player except items (no healing after fights, on new floors or on level ups).
- Equipment slots: weapon, head, body, legs, shoes and two accessories.
- Art: three CC0 packs, listed in assets/CREDITS.md. Floors use the themes stone, jungle and desert.
- Running the game at the exhibit: docs/EXHIBIT.md.

## Updates (16 Nov 2026)
- New game is now: name -> class -> dungeon -> welcome + level -> floor 1. Esc goes back one screen. The order is in core/flow.py.
- Dungeons and levels are listed in data/dungeons.json. Only the German Dungeon is open; the others are placeholders.
- One question bank per level: questions/data/questions_german_a1.json, _a2.json, _b1.json. A1 and A2 are empty for now and locked in the menu. The rule for "can this level be played" is systems/dungeons.is_playable().
- The run remembers the hero's name, the subject and the level. SAVE_VERSION is 4, so saves from older builds no longer load.
- The demo (F1) skips the new screens and plays German B1.
- Every move has its own simple look in a fight (combat/skill_looks.py): arcs, flying orbs or streaks, falling meteors or arrows, or a ring for utility moves. Colours, sizes, counts and screen shake are in data/skill_looks.json. They are pictures only: a green Poison Arrow does not poison anything until B writes that rule. A basic start, meant to be improved by the team.

## Updates (24-25 Nov 2026, C)
- Knowledge tracing (BKT) is in ai/mastery.py and topic choice in QuestionEngine._choose (C). Every topic now starts at 20% on the Progress screen.
- Contract: KnowledgeTracker.update(topic, correct) gained a third argument, guess=0.25 (the chance of a lucky right answer). Old calls still work. The engine passes 1/choices for multiple choice, and lower values for tick-all and typed answers.
- The BKT numbers and the review weight are in data/progression.json, under "mastery".

## Updates (25 Nov 2026)
- German A1 is playable: questions/data/questions_german_a1.json, 3,943 questions from Das Leben A1, Einheiten 1–16. It is the first level on the level screen now. A2 is still empty.
- A bank can now say which Einheiten each floor asks ("floor_einheiten"). A1: floor 1 = Einheiten 1–5, floor 2 = 1–10, floor 3 = 1–16. B1 has no such entry and works as before. New method: QuestionEngine.last_einheit(floor).
- questions/build/build.py builds every level (python build.py, or python build.py a1). The B1 output is unchanged.
- D: the bosses ask B1 grammar topics, which A1 doesn't have, so in A1 they ask any topic. A1 boss topics could be added later.

## Updates (25 Nov 2026, sound)
- Sound and music are in, all made in code: tools/make_sounds.py turns the recipes in data/sounds.json into assets/sounds/*.wav. No downloaded sounds, so no licences.
- Play an effect from any screen with sound.play("name") (core/sound.py). A screen picks its music with a class attribute: music = "dungeon"; None keeps the current track; "off" is silence.
- F2 turns sound on and off on every screen. With no sound card, the game just stays quiet.

## Updates (26 Nov 2026, play-test changes)
- Title logo: put a drawn assets/sprites/logo.png in, and the title uses it (see assets/README.md). Without it, the logo is made from the font.
- Rooms: new kinds pillars (a hall with pillars), storeroom (a chest, no monsters) and merchant (a wandering shop). Monsters are spread so every normal and pillar room gets one first. Weights and chances are in data/rooms.json (A can tune them).
- Wandering merchant: on about half the floors one room has a merchant. Walk into him to trade; Esc goes back to the dungeon. His stock is wandering_stock in data/shop.json. Nobody can walk through his tile (Floor.is_walkable).
- Shops can sell now: Tab switches Buy / Sell. Worn equipment is not sold (take it off first). The shopkeeper breathes and hops after a sale (ui/merchant.py).
- Bag: Delete (or Backspace) on a bag item asks first, a second press throws it away. On a worn item it still takes it off.
- Streak: "Streak x3 +30% damage" with boxes up to the biggest bonus, in fights and on the map.
- Music: each floor look has its own tune (data/themes.json, music: stone, jungle, desert) and the boss room has its own (boss_room). DungeonScene.music is now a property.

