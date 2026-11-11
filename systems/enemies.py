"""Enemy stats for combat (owner: D). No pygame here. Numbers come from data/enemies.json."""
import json
import random
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
    elite: bool = False         # a stronger version of a normal enemy with better loot
    large_art: bool = False     # its pictures are 32 pixels wide, so it is never drawn extra big

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount) -> int:
        lost = min(self.hp, max(0, amount))
        self.hp -= lost
        return lost


def make_enemy(enemy_id, elite=False) -> Enemy:
    """Build an enemy from data/enemies.json. An elite gets its numbers multiplied (see elite_rules)."""
    s = _data()["enemies"][enemy_id]
    enemy = Enemy(id=enemy_id, name=s["name"], hp=s["hp"], max_hp=s["hp"], damage=s["damage"],
                  xp=s["xp"], gold=s["gold"], topics=list(s.get("topics", [])),
                  color=tuple(s.get("color", (200, 80, 80))), boss=s.get("boss", False),
                  loot_table=s.get("loot", "boss" if s.get("boss") else "enemy"),
                  large_art=s.get("large_art", False))
    if elite:
        rules = elite_rules()
        enemy.elite = True
        enemy.hp = enemy.max_hp = round(enemy.hp * rules["hp"])
        enemy.damage = round(enemy.damage * rules["damage"])
        enemy.xp = round(enemy.xp * rules["xp"])
        enemy.gold = round(enemy.gold * rules["gold"])
        enemy.loot_table = rules["loot"]
    return enemy


def elite_rules() -> dict:
    """{"chance", "hp", "damage", "xp", "gold", "loot"}: how elites differ from normal enemies."""
    return _data()["elite"]


def floor_spawns(floor_number) -> dict:
    """{"count": n, "pool": [enemy ids], "boss": enemy id} for one floor."""
    return _data()["floors"][str(floor_number)]


def chase_rules() -> dict:
    """How monsters on the map chase the player: {"wake_radius", "sleep_radius", "seconds_per_step", "rest_after_flee"}."""
    return _data()["chase"]


def floor_theme(floor_number, seed=0) -> dict:
    """How a floor looks: {"folder": ..., "background": [r, g, b]} from data/themes.json.

    A floor can list several themes. Then the run's seed picks one, so different runs
    look different but the same run always looks the same.
    """
    themes = json.loads((DATA_PATH.parent / "themes.json").read_text(encoding="utf-8"))["themes"]
    choice = floor_spawns(floor_number).get("theme", "stone")
    names = choice if isinstance(choice, list) else [choice]
    name = random.Random(f"theme-{seed}-{floor_number}").choice(names)
    return themes.get(name, themes["stone"])
