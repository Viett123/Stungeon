"""The dungeons (school subjects) and their levels, from data/dungeons.json (owner: lead). No pygame here.

Every level has its own question bank file in questions/data/. A level can only be
started when its bank has questions; an empty bank (A1 and A2 for now) shows as
"coming soon" on the level screen instead of crashing the first fight.
"""
import json
from pathlib import Path

from systems.player import load_data

BANK_DIR = Path(__file__).resolve().parent.parent / "questions" / "data"


def all_dungeons() -> list[dict]:
    """Every dungeon in the order the menu shows them, including the ones still in development."""
    return load_data("dungeons.json")["dungeons"]


def get_dungeon(subject) -> dict:
    for dungeon in all_dungeons():
        if dungeon["id"] == subject:
            return dungeon
    raise KeyError(subject)


def default_choice() -> tuple[str, str]:
    """(subject, level) used when nothing was picked: the exhibit demo and old code paths."""
    default = load_data("dungeons.json")["default"]
    return default["subject"], default["level"]


def bank_path(subject, level) -> Path:
    """The question bank file for one level of one dungeon."""
    for entry in get_dungeon(subject)["levels"]:
        if entry["id"] == level:
            return BANK_DIR / entry["bank"]
    raise KeyError(f"{subject} {level}")


def question_count(subject, level) -> int:
    """How many questions the level's bank has (0 if the file is missing)."""
    path = bank_path(subject, level)
    if not path.exists():
        return 0
    return len(json.loads(path.read_text(encoding="utf-8"))["questions"])


def is_playable(subject, level) -> bool:
    """Can a run be started on this level? The ONE place this rule lives.

    For now: the dungeon is available and its bank is not empty.
    TODO(C): when A1/A2 are half-filled, tighten this (for example: every floor
    needs easy, medium and hard questions), or the first fight may find none.
    """
    try:
        return get_dungeon(subject)["available"] and question_count(subject, level) > 0
    except KeyError:
        return False
