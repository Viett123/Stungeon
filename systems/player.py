"""The player (owner: D). No pygame here.

Numbers come from data/classes.json and data/progression.json.
Contract additions (new public methods): take_damage, heal, spend, gain_resource.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data(name):
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
    max_resource: int = 0
    name: str = ""          # what the player called their character on the new-game screen

    def __post_init__(self):
        stats = load_data("classes.json")["classes"][self.class_id]
        self.class_name = stats["name"]
        self.resource_name = stats["resource"]
        self.color = tuple(stats.get("color", (90, 180, 230)))
        progression = load_data("progression.json")
        self.max_hp = self.max_hp or stats["base_hp"] + progression["hp_per_level"] * (self.level - 1)
        self.hp = self.hp or self.max_hp
        self.max_resource = self.max_resource or stats["max_resource"]
        self.resource = self.resource or stats["start_resource"]

    # --- moves -------------------------------------------------------------
    def unlocked_moves(self) -> list[dict]:
        """Every move this class has at this level, with its tier info merged in."""
        data = load_data("moves.json")
        moves = []
        for move in data["moves"]:
            tier = data["tiers"][move["tier"]]
            if move["class"] == self.class_id and tier["unlock_level"] <= self.level:
                moves.append({**tier, **move})
        return moves

    def damage_multiplier(self) -> float:
        return 1.0   # TODO(D): weapons, buffs and debuffs

    # --- hp and resource ---------------------------------------------------
    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount) -> int:
        """Lose hp (never below 0). Returns how much was actually lost."""
        lost = min(self.hp, max(0, amount))
        self.hp -= lost
        return lost

    def heal(self, amount) -> int:
        gained = min(self.max_hp - self.hp, max(0, amount))
        self.hp += gained
        return gained

    def spend(self, amount) -> bool:
        """Pay a move's cost. Returns False (and pays nothing) if there is not enough."""
        if amount > self.resource:
            return False
        self.resource -= amount
        return True

    def gain_resource(self, amount):
        self.resource = min(self.max_resource, self.resource + amount)

    # --- xp and levels -----------------------------------------------------
    def gain_xp(self, amount) -> list[str]:
        """Add xp. Returns events like "level_up:3" and "unlocked:fireball"."""
        progression = load_data("progression.json")
        self.xp += amount
        events = []
        while self.level < progression["max_level"] and self.xp >= progression["xp_for_level"][str(self.level + 1)]:
            before = {m["id"] for m in self.unlocked_moves()}
            self.level += 1
            # Only max HP grows. Current HP stays: nothing heals the player except items.
            self.max_hp += progression["hp_per_level"]
            events.append(f"level_up:{self.level}")
            events += [f"unlocked:{m['id']}" for m in self.unlocked_moves() if m["id"] not in before]
        return events

    def _equipped_items(self) -> list[dict]:
        items = load_data("items.json")["items"]
        return [items[item_id] for item_id in self.equipped.values() if item_id in items]

    def damage_multiplier(self) -> float:
        """Product of every equipped item's damage_multiplier (1.0 if it has none).
        A weapon of another class counts for less (item_damage_multiplier)."""
        result = 1.0
        for item in self._equipped_items():
            result *= self.item_damage_multiplier(item)
        return result

    def off_class(self, item) -> bool:
        """True for a weapon made for another class (its "class" in items.json is not ours)."""
        return item.get("slot") == "weapon" and item.get("class", self.class_id) != self.class_id

    def item_damage_multiplier(self, item) -> float:
        """What this one item does to our damage. A weapon of another class still helps, but its
        bonus is multiplied by off_class_damage in data/items.json, so a mage with a mace hits
        weaker than with a staff of the same rarity."""
        multiplier = item.get("damage_multiplier", 1.0)
        if self.off_class(item):
            multiplier *= load_data("items.json")["off_class_damage"]
        return multiplier

    def defense(self) -> int:
        """Total damage removed from every enemy hit by the equipped items."""
        return sum(item.get("defense", 0) for item in self._equipped_items())

    def bonus_seconds(self) -> int:
        """Extra seconds to answer every question, from the equipped items ("bonus_seconds" in items.json)."""
        return sum(item.get("bonus_seconds", 0) for item in self._equipped_items())
