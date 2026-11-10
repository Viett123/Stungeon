"""Save and load (owner: D). No pygame here.

The game is saved once per floor. `state` is a plain dict, so it can be written as JSON.
"""
import json
from pathlib import Path

SAVE_PATH = Path(__file__).resolve().parent.parent / "saves" / "save.json"


def save_game(state):
    SAVE_PATH.parent.mkdir(exist_ok=True)
    SAVE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_game() -> dict:
    """Return the saved state, or {} when there is no save yet."""
    if not SAVE_PATH.exists():
        return {}
    return json.loads(SAVE_PATH.read_text(encoding="utf-8"))
