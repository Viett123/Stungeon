"""What using an item does (owner: D). No pygame here.

PLACEHOLDER. The inventory calls apply() when the player uses a consumable.
Only two simple effects exist so potions can be tried: "heal" and "resource".
"""


def apply(item, player) -> bool:
    """Use the item on the player. Return True if it did something.

    Returning False means "nothing happened" (for example a potion at full HP).
    The inventory then keeps the item instead of wasting it.
    """
    effect = item.get("effect", {})
    kind = effect.get("type")
    if kind == "heal":
        return player.heal(effect["amount"]) > 0
    if kind == "resource":
        before = player.resource
        player.gain_resource(effect["amount"])
        return player.resource > before
    # TODO(D): scrolls, buffs and the other effects from the design doc.
    # TODO(D): equipment bonuses do not go here. They belong in Player.damage_multiplier()
    #          and in combat/damage.py (ask B), using player.equipped.
    return False
