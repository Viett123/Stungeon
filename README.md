# Stungeon

An educational dungeon-crawler RPG: answer German B1 questions to fight. Python 3.11+ and pygame-ce.

## Setup

```
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

A window with the title screen should open. Press Enter to walk around floor 1.

Run the tests with `python -m pytest`.

## Where things are

See the Team Guides doc for roles, the shared contract and the git workflow, and
[docs/HANDOFF.md](docs/HANDOFF.md) for the key decisions. Rules for Claude Code are in [CLAUDE.md](CLAUDE.md).

Every module from the shared contract exists already as a placeholder that returns fake data.
Look for `TODO(A)`, `TODO(B)`, `TODO(C)`, `TODO(D)` to find your part.
