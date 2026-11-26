"""Buying and selling: in the shop between floors, or from a wandering merchant (owner: D). No pygame here."""
import random

from systems import inventory, items
from systems.player import load_data


def stock(floor_number) -> list[str]:
    """Item ids the shop sells after this floor. An empty list means: no shop."""
    return list(load_data("shop.json")["stock"].get(str(floor_number), []))


def wandering_stock(floor_number, seed=0) -> list[str]:
    """Item ids a wandering merchant sells on this floor: a random mix (he can stand in any room).

    He always has the items under "always"; the others are picked at random from every item,
    rarer ones less often (data/shop.json, "wandering"). No item is picked twice.
    seed: the run's seed. The same run and floor always give the same items, so the player
    cannot leave and come back to get new ones. random.Random(...) is our own dice, so the
    game's other random numbers are not changed by it.
    """
    rules = load_data("shop.json")["wandering"]
    weights = rules["rarity_weights"].get(str(floor_number)) or rules["rarity_weights"][max(rules["rarity_weights"], key=int)]
    chosen = list(rules["always"])
    pool = [item_id for item_id, item in load_data("items.json")["items"].items()
            if item_id not in chosen and weights.get(item.get("rarity"), 0) > 0]
    rng = random.Random(f"{seed}-merchant-{floor_number}")
    while pool and len(chosen) < len(rules["always"]) + rules["items"]:
        pick = rng.choices(pool, weights=[weights[items.get_item(i)["rarity"]] for i in pool])[0]
        chosen.append(pick)
        pool.remove(pick)
    return chosen


def buy_price(item) -> int:
    return item["price"]


def sell_price(item) -> int:
    return int(item["price"] * items.sell_ratio())


def buy(player, item_id) -> str:
    """Try to buy one item. Returns "ok", "no_gold" or "full"."""
    item = items.get_item(item_id)
    if player.gold < buy_price(item):
        return "no_gold"
    if not inventory.add_item(player, item_id):
        return "full"
    player.gold -= buy_price(item)
    return "ok"


def sell(player, item_id) -> bool:
    """Sell one item from the bag. Returns False if the player does not have it."""
    if not inventory.remove_item(player, item_id):
        return False
    player.gold += sell_price(items.get_item(item_id))
    return True
