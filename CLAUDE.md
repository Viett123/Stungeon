# Stungeon
Educational dungeon-crawler RPG in Python 3.11 + pygame-ce. English UI.

## Rules
- Only change files in the folder of the task you are given.
- Follow the shared contract in the Team Guides doc. Never change a public function signature without saying so.
- All balancing numbers go in data/*.json, never hardcoded.
- All on-screen text comes from core/strings_en.json.
- ai/, questions/ and systems/ must never import pygame.
- Screen 1280x720, 60 FPS, tiles 16 px drawn at 3x (48 px). Map grid is grid[y][x].
- Never block the game loop (no time.sleep, no input()).
- Add or update a test in tests/ for every logic change. Run: python -m pytest
- Explain every change in plain English for a first-year student.

## Question format
See questions/README.md. Topics and difficulties must match the bank exactly.

## Docs
- Handoff notes (decisions, scope, deadlines): docs/HANDOFF.md
- Project Overview (game design): https://claude.ai/artifact/KFh6efHhWKdX2pZqXmXvij
- Team Guides (roles, shared contract, git workflow): https://claude.ai/artifact/CWoDxFi7LUu9j99jkQdYDR
