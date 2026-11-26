"""Adding, removing, using and equipping items (owner: D). No pygame here.

player.inventory is a list of item ids (the bag). The same id can be in it more than once.
The bag has inventory_size SLOTS. Copies of the same item share a slot, up to its stack size
(10 potions in one slot, see stack_size in data/items.json), so the list itself can be longer
than the number of slots. stacks() says how the list is laid out in slots.
player.equipped is a dict from slot name to item id, e.g. {"weapon": "old_sword", "head": "cloth_hood"}.

An equipment item names the KIND of slot it fits in its "slot" field (data/items.json):
weapon, head, body, legs, shoes or accessory. There are two accessory slots.
"""
from systems import item_effects, items

ACCESSORY_SLOTS = ["accessory_1", "accessory_2"]
EQUIP_SLOTS = ["weapon", "head", "body", "legs", "shoes"] + ACCESSORY_SLOTS
SLOT_KINDS = ["weapon", "head", "body", "legs", "shoes", "accessory"]   # what an item's "slot" may say


def stacks(player) -> list[tuple[str, int]]:
    """The bag as slots: [(item id, how many), ...], each item in the order it was first picked up.

    Example with a stack size of 10: 12 small potions and a sword are
    [("small_potion", 10), ("small_potion", 2), ("old_sword", 1)]: three slots.
    """
    order = []
    for item_id in player.inventory:
        if item_id not in order:
            order.append(item_id)
    result = []
    for item_id in order:
        left, size = player.inventory.count(item_id), items.stack_size(item_id)
        while left > 0:
            result.append((item_id, min(size, left)))
            left -= size
    return result


def slots_used(player) -> int:
    return len(stacks(player))


def is_full(player) -> bool:
    """True if every slot is taken. (A potion may still fit on top of a stack that is not full: see can_add.)"""
    return slots_used(player) >= items.inventory_size()


def can_add(player, item_id) -> bool:
    """Is there room for one more of this item: a stack of it with space left, or an empty slot?"""
    if player.inventory.count(item_id) % items.stack_size(item_id):
        return True                      # its last stack is not full yet
    return not is_full(player)


def add_item(player, item_id) -> bool:
    """Put an item in the bag. Returns False if there is no room for it."""
    if not can_add(player, item_id):
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
        player.inventory.append(old)   # always fits: the item we took out freed its own slot
    player.equipped[slot] = item_id
    return True


def unequip(player, slot) -> bool:
    """Move the item in a slot back into the bag. Returns False if the slot is empty or the bag is full."""
    if slot not in player.equipped or is_full(player):
        return False
    player.inventory.append(player.equipped.pop(slot))
    return True
