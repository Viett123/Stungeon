"""Adding, removing, using and equipping items (owner: D). No pygame here.

player.inventory is a list of item ids (the bag). The same id can be in it more than once.
player.equipped is a dict from slot name to item id, e.g. {"weapon": "old_sword", "head": "cloth_hood"}.

An equipment item names the KIND of slot it fits in its "slot" field (data/items.json):
weapon, head, body, legs, shoes or accessory. There are two accessory slots.
"""
from systems import item_effects, items

ACCESSORY_SLOTS = ["accessory_1", "accessory_2"]
EQUIP_SLOTS = ["weapon", "head", "body", "legs", "shoes"] + ACCESSORY_SLOTS
SLOT_KINDS = ["weapon", "head", "body", "legs", "shoes", "accessory"]   # what an item's "slot" may say


def is_full(player) -> bool:
    return len(player.inventory) >= items.inventory_size()


def add_item(player, item_id) -> bool:
    """Put an item in the bag. Returns False if the bag is full."""
    if is_full(player):
        return False
    player.inventory.append(item_id)
    return True


def remove_item(player, item_id) -> bool:
    """Take one copy of the item out of the bag. Returns False if it is not there."""
    if item_id not in player.inventory:
        return False
    player.inventory.remove(item_id)
    return True


def use_item(player, item_id) -> bool:
    """Use a consumable from the bag. It is only used up if it did something."""
    if item_id not in player.inventory:
        return False
    item = items.get_item(item_id)
    if item["kind"] != "consumable" or not item_effects.apply(item, player):
        return False
    player.inventory.remove(item_id)
    return True


def slot_for(player, item) -> str:
    """The slot an equipment item goes into.

    An accessory takes the first empty accessory slot. If both are full, it replaces
    the one in the first slot.
    """
    if item["slot"] != "accessory":
        return item["slot"]
    for slot in ACCESSORY_SLOTS:
        if slot not in player.equipped:
            return slot
    return ACCESSORY_SLOTS[0]


def equip(player, item_id) -> bool:
    """Move equipment from the bag into its slot. What was in the slot goes back into the bag."""
    if item_id not in player.inventory:
        return False
    item = items.get_item(item_id)
    if item["kind"] != "equipment":
        return False
    slot = slot_for(player, item)
    player.inventory.remove(item_id)
    old = player.equipped.get(slot)
    if old:
        player.inventory.append(old)   # always fits: we just took one item out
    player.equipped[slot] = item_id
    return True


def unequip(player, slot) -> bool:
    """Move the item in a slot back into the bag. Returns False if the slot is empty or the bag is full."""
    if slot not in player.equipped or is_full(player):
        return False
    player.inventory.append(player.equipped.pop(slot))
    return True
