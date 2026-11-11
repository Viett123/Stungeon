"""Loot drops (owner: D). No pygame here. The tables are in data/loot_tables.json."""
from systems.player import load_data


def roll_loot(table_id, rng) -> list[str]:
    """Roll once for every entry of the table. Returns the item ids that dropped.

    Always pass the run's rng (not the random module), so a run with the same seed
    drops the same loot.
    """
    table = load_data("loot_tables.json")["tables"].get(table_id, [])
    return [entry["item"] for entry in table if rng.random() < entry["chance"]]


def roll_chest_gold(rng) -> int:
    """How much gold a chest holds: a number between the two values of chest_gold."""
    low, high = load_data("loot_tables.json")["chest_gold"]
    return rng.randint(low, high)
