"""On-screen text checks (no pygame needed)."""
import json
import re
import string
from pathlib import Path

from questions.engine import BANK_PATH

ROOT = Path(__file__).resolve().parent.parent
STRINGS = json.loads((ROOT / "core" / "strings_en.json").read_text(encoding="utf-8"))
REPLACED = {"→"}   # ui/widgets.py swaps these for plain characters when drawing


def test_every_t_key_used_in_code_exists():
    used = set()
    for path in ROOT.glob("*/*.py"):
        if ".venv" in path.parts:
            continue
        used |= set(re.findall(r'\bt\(\s*"([a-z0-9_]+)"', path.read_text(encoding="utf-8")))
    missing = {k for k in used if k not in STRINGS}
    assert not missing


def test_no_string_uses_a_placeholder_called_key():
    # t(key, **values): a "{key}" placeholder would clash with t's own parameter.
    for text in STRINGS.values():
        names = {name for _, name, _, _ in string.Formatter().parse(text) if name}
        assert "key" not in names


def test_question_bank_only_uses_characters_the_font_can_draw():
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    for q in bank["questions"]:
        parts = [q["question"], q.get("explanation", "")] + list(q.get("choices", []))
        for char in "".join(parts):
            assert ord(char) < 256 or char in REPLACED, f"{q['id']} has {char!r}"
