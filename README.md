# Stungeon

An educational dungeon-crawler RPG: answer German B1 questions to fight. Python 3.11+ and pygame-ce.

## Setup

```
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

A window with the title screen should open.

## How to play (prototype)

1. On the title menu choose New game (or Continue, or the Demo with F1), then pick a class.
2. Walk with the arrow keys or WASD (hold a key to keep walking). Walk into an enemy to fight it.
   Monsters that see you within 2 tiles run after you and attack. Walk into a chest to open it.
   Nothing heals you except potions: drink them from your bag (I), also in a fight.
   The floor is hidden until you explore it; the small map shows where you have been.
   Gold rings mark elite monsters. A mini-boss guards the treasure room. Spikes hurt.
3. In a fight, pick a move with the number keys. Stronger moves ask harder German questions.
   A wrong answer is a miss, but the move's cost is still spent, and the enemy still hits back.
4. Beat the boss standing on the stairs, step on the stairs, and go down. Clear floor 3 to win.
5. Between floors there is a shop, then a choice with a risk and a reward.
   Press I for your bag, M for your progress and Esc for the pause menu.
   The game is saved every time a floor starts.

Typed answers ignore upper/lower case, and you can type ae/oe/ue/ss instead of ä/ö/ü/ß.

Run the tests with `python -m pytest`.

## Where things are

See the Team Guides doc for roles, the shared contract and the git workflow, and
[docs/HANDOFF.md](docs/HANDOFF.md) for the key decisions. Rules for Claude Code are in [CLAUDE.md](CLAUDE.md).

Every module from the shared contract exists already as a placeholder that returns fake data.
Look for `TODO(A)`, `TODO(B)`, `TODO(C)`, `TODO(D)` to find your part.

To put the game on the exhibit laptop, see [docs/EXHIBIT.md](docs/EXHIBIT.md).
