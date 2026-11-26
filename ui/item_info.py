"""Turns an item into the text lines shown in the bag and the shop (owner: B).

Both screens use this, so an item is always described the same way.
"""
from core.strings import t
from systems.player import load_data
from ui import slots, theme

RARITY_COLORS = {
    "common": theme.TEXT,
    "uncommon": (124, 186, 110),
    "rare": (96, 150, 220),
    "epic": (176, 110, 210),
    "legendary": (230, 160, 60),
}


def kind_text(item):
    """"Consumable", or the slot an equipment item fits: "Weapon", "Head", "Accessory", ..."""
    if item["kind"] == "consumable":
        return t("kind_consumable")
    return t(f"slot_{item['slot']}")


def item_lines(item, player=None):
    """[(text, colour), ...]: name, then rarity and kind, then the description.
    With a player (added later, so old calls still work), a weapon gets one more line: which
    class it is made for, and in red how much weaker it is when it is not the player's class."""
    rarity = item["rarity"]
    lines = [
        (item["name"], RARITY_COLORS.get(rarity, theme.TEXT)),
        (t("item_rarity_kind", rarity=t(f"rarity_{rarity}"), kind=kind_text(item)), theme.TEXT_DIM),
        (item["text"], theme.TEXT),
    ]
    line = class_line(item, player)
    if line:
        lines.append(line)
    return lines


def percent(multiplier) -> str:
    """1.19 -> "+19%", 0.89 -> "-11%"."""
    return f"{round((multiplier - 1) * 100):+d}%"


def class_line(item, player):
    """For a weapon: "Made for: Mage" (dim), or, when the player is another class, the debuff in red.
    None for anything that is not a weapon with a class, or without a player."""
    if player is None or item.get("slot") != "weapon" or "class" not in item:
        return None
    made_for = load_data("classes.json")["classes"][item["class"]]["name"]
    if not player.off_class(item):
        return (t("item_made_for", cls=made_for), theme.TEXT_DIM)
    return (t("item_off_class", cls=made_for, you=player.class_name,
              damage=percent(player.item_damage_multiplier(item)),
              normal=percent(item.get("damage_multiplier", 1.0))), theme.BAD)


def item_icon(item, font):
    """The picture assets/sprites/item_<id>.png, or a coloured square with two letters."""
    return slots.icon_for(f"item_{item['id']}", tuple(item.get("color", theme.STONE)), item["name"][:2], font)
