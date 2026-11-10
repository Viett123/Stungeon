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
