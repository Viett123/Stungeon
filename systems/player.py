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
