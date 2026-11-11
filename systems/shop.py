"""Buying and selling between floors (owner: D). No pygame here."""
from systems import inventory, items
from systems.player import load_data


def stock(floor_number) -> list[str]:
    """Item ids the shop sells after this floor. An empty list means: no shop."""
    return list(load_data("shop.json")["stock"].get(str(floor_number), []))


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
