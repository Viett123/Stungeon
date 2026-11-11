"""All on-screen text, loaded once from core/strings_en.json.

Use:  from core.strings import t
      t("level_up", level=3)   ->  "Level up! You are now level 3."
"""
import json
from pathlib import Path

_STRINGS = json.loads((Path(__file__).parent / "strings_en.json").read_text(encoding="utf-8"))


def t(key, **values):
    """Return the English text for `key`, filling in {placeholders} from `values`."""
    text = _STRINGS.get(key, f"[{key}]")   # a missing key shows on screen instead of crashing
    return text.format(**values) if values else text
