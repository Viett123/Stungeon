"""Bag, shop and loot logic. Item ids and prices are read from the data files,
so these tests keep working when owner D replaces the placeholder items."""
import random

from systems import inventory, items, shop
from systems.loot import roll_loot
from systems.player import Player, load_data

ALL = load_data("items.json")["items"]
CONSUMABLE = next(i for i, item in ALL.items() if item["kind"] == "consumable" and item["effect"]["type"] == "heal")
WEAPONS = [i for i, item in ALL.items() if item.get("slot") == "weapon"]


def test_bag_has_a_size_limit():
    player = Player("warrior")
    for _ in range(items.inventory_size()):
        assert inventory.add_item(player, CONSUMABLE)
    assert inventory.is_full(player)
    assert not inventory.add_item(player, CONSUMABLE)


def test_healing_item_is_used_up_only_if_it_heals():
    player = Player("warrior")
    inventory.add_item(player, CONSUMABLE)
    assert not inventory.use_item(player, CONSUMABLE)          # full HP: nothing happens
    assert player.inventory == [CONSUMABLE]
    player.take_damage(30)
    assert inventory.use_item(player, CONSUMABLE)
    assert player.inventory == [] and player.hp > player.max_hp - 30


def test_cannot_use_what_you_do_not_have():
    assert not inventory.use_item(Player("mage"), CONSUMABLE)


def test_equip_and_unequip():
    player = Player("archer")
    weapon = WEAPONS[0]
    inventory.add_item(player, weapon)
    assert inventory.equip(player, weapon)
    assert player.equipped == {"weapon": weapon} and player.inventory == []
    assert inventory.unequip(player, "weapon")
    assert player.equipped == {} and player.inventory == [weapon]
    assert not inventory.unequip(player, "weapon")              # the slot is empty now


def test_equipping_swaps_the_old_item_back_into_the_bag():
    player = Player("archer")
    weapon = WEAPONS[0]
    inventory.add_item(player, weapon)
    inventory.add_item(player, weapon)
    inventory.equip(player, weapon)
    inventory.equip(player, weapon)
    assert player.equipped == {"weapon": weapon} and player.inventory == [weapon]


def test_a_consumable_cannot_be_equipped():
    player = Player("mage")
    inventory.add_item(player, CONSUMABLE)
    assert not inventory.equip(player, CONSUMABLE)


def test_buy_needs_gold_and_space():
    player = Player("mage")
    price = shop.buy_price(items.get_item(CONSUMABLE))
    assert shop.buy(player, CONSUMABLE) == "no_gold"
    player.gold = price
    assert shop.buy(player, CONSUMABLE) == "ok"
    assert player.gold == 0 and player.inventory == [CONSUMABLE]
    player.gold = price
    player.inventory = [CONSUMABLE] * items.inventory_size()
    assert shop.buy(player, CONSUMABLE) == "full"
    assert player.gold == price                                  # nothing was paid


def test_sell_gives_gold_back():
    player = Player("mage")
    inventory.add_item(player, CONSUMABLE)
    assert shop.sell(player, CONSUMABLE)
    assert player.gold == shop.sell_price(items.get_item(CONSUMABLE)) and player.inventory == []
    assert not shop.sell(player, CONSUMABLE)


def test_shop_stock_and_loot_tables_only_name_real_items():
    for stock in load_data("shop.json")["stock"].values():
        assert set(stock) <= set(ALL)
    for table in load_data("loot_tables.json")["tables"].values():
        assert {entry["item"] for entry in table} <= set(ALL)
    assert shop.stock(999) == []                                 # no entry = no shop


def test_loot_is_the_same_for_the_same_seed():
    assert roll_loot("boss", random.Random(5)) == roll_loot("boss", random.Random(5))
    assert roll_loot("no_such_table", random.Random(5)) == []
