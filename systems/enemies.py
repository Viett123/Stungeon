"""Enemy stats for combat (owner: D). No pygame here. Numbers come from data/enemies.json."""
import json
from dataclasses import dataclass
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "enemies.json"


def _data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@dataclass
class Enemy:
    id: str
    name: str
    hp: int
    max_hp: int
    damage: int
    xp: int
    gold: int
    topics: list
    color: tuple
    boss: bool = False
    loot_table: str = "enemy"   # which table in data/loot_tables.json this enemy drops from

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount) -> int:
        lost = min(self.hp, max(0, amount))
        self.hp -= lost
        return lost


def make_enemy(enemy_id) -> Enemy:
    s = _data()["enemies"][enemy_id]
    return Enemy(id=enemy_id, name=s["name"], hp=s["hp"], max_hp=s["hp"], damage=s["damage"],
                 xp=s["xp"], gold=s["gold"], topics=list(s.get("topics", [])),
                 color=tuple(s.get("color", (200, 80, 80))), boss=s.get("boss", False),
                 loot_table=s.get("loot", "boss" if s.get("boss") else "enemy"))


def floor_spawns(floor_number) -> dict:
    """{"count": n, "pool": [enemy ids], "boss": enemy id} for one floor."""
    return _data()["floors"][str(floor_number)]
