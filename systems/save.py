"""Save and load (owner: D). No pygame here.

The game is saved once per floor. `state` is a plain dict, so it can be written as JSON.
What goes into the dict is decided in core/run.py (run_to_dict).
"""
import json
import sys
from pathlib import Path

# In a built exe (tools/build.py) the save goes next to Stungeon.exe; otherwise into the repo folder.
_BASE = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
SAVE_PATH = _BASE / "saves" / "save.json"


def save_game(state):
    SAVE_PATH.parent.mkdir(exist_ok=True)
    SAVE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_game() -> dict:
    """Return the saved state, or {} when there is no save or the file is damaged."""
    if not SAVE_PATH.exists():
        return {}
    try:
        return json.loads(SAVE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}   # a broken save file must not crash the game


def has_save() -> bool:
    return bool(load_game())


def delete_save():
    if SAVE_PATH.exists():
        SAVE_PATH.unlink()
