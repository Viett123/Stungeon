"""Turns an item into the text lines shown in the bag and the shop (owner: B).

Both screens use this, so an item is always described the same way.
"""
from core.strings import t
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


def item_lines(item):
    """[(text, colour), ...]: name, then rarity and kind, then the description."""
    rarity = item["rarity"]
    return [
        (item["name"], RARITY_COLORS.get(rarity, theme.TEXT)),
        (t("item_rarity_kind", rarity=t(f"rarity_{rarity}"), kind=kind_text(item)), theme.TEXT_DIM),
        (item["text"], theme.TEXT),
    ]


def item_icon(item, font):
    """The picture assets/sprites/item_<id>.png, or a coloured square with two letters."""
    return slots.icon_for(f"item_{item['id']}", tuple(item.get("color", theme.STONE)), item["name"][:2], font)
