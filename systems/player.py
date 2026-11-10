"""The player (owner: D). No pygame here.

PLACEHOLDER: stats come from data/classes.json, levelling up is not done yet.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


@dataclass
class Player:
    class_id: str
    level: int = 1
    xp: int = 0
    gold: int = 0
    inventory: list = field(default_factory=list)
    equipped: dict = field(default_factory=dict)
    hp: int = 0
    max_hp: int = 0
    resource: int = 0

    def __post_init__(self):
        stats = _load("classes.json")["classes"][self.class_id]
        self.max_hp = self.max_hp or stats["base_hp"]
        self.hp = self.hp or self.max_hp
        self.resource = self.resource or stats["base_resource"]

    def unlocked_moves(self) -> list[dict]:
        data = _load("moves.json")
        tiers = data["tiers"]
        return [m for m in data["moves"]
                if m["class"] == self.class_id and tiers[m["tier"]]["unlock_level"] <= self.level]

    def damage_multiplier(self) -> float:
        return 1.0   # TODO(D): weapons, buffs and debuffs

    def gain_xp(self, amount) -> list[str]:
        self.xp += amount
        return []    # TODO(D): level ups, returns events like "level_up", "unlocked:fireball"
