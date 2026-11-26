"""Reads items from data/items.json (owner: D). No pygame here."""
from systems.player import load_data


def get_item(item_id) -> dict:
    """The item's data plus its id, e.g. {"id": "small_potion", "name": "Small Potion", ...}."""
    return dict(load_data("items.json")["items"][item_id], id=item_id)


def inventory_size() -> int:
    return load_data("items.json")["inventory_size"]


def stack_size(item_id) -> int:
    """How many of this item fit in one bag slot: 10 for potions, 1 for equipment (data/items.json)."""
    sizes = load_data("items.json").get("stack_size", {})
    return max(1, sizes.get(get_item(item_id)["kind"], 1))


def sell_ratio() -> float:
    """Share of the price you get back when selling."""
    return load_data("items.json")["sell_ratio"]
