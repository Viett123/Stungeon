"""Turns a move into text lines and a hotbar entry (owner: B).

Used by the hotbar tooltip and by the combat screen, so both always say the same thing.
"""
from core.strings import t
from ui import slots, theme


def damage_text(move):
    if move["questions"] == 0:
        return t("move_no_question")
    if move["questions"] > 1:
        return t("move_damage_ultimate", damage=move["damage"], n=move["questions"])
    return t("move_damage", damage=move["damage"])


def move_lines(move, resource_name):
    """[(text, colour), ...] describing a move: name, tier, damage, cost."""
    affordable = move.get("affordable", True)
    return [
        (move["name"], theme.GOLD),
        (t(f"tier_{move['tier']}"), theme.TEXT),
        (damage_text(move), theme.TEXT),
        (t("move_cost", cost=move["cost"], resource=resource_name), theme.TEXT if affordable else theme.BAD),
    ]


def initials(name):
    """"Shield Bash" -> "SB", "Slash" -> "Sl". Drawn on placeholder icons."""
    words = name.split()
    if len(words) > 1:
        return words[0][0] + words[1][0]
    return name[:2]


def hotbar_entries(moves, resource_name, font):
    """One hotbar entry per move."""
    return [{
        "icon": slots.icon_for(f"icon_{move['id']}", theme.TIER_COLORS[move["tier"]], initials(move["name"]), font),
        "enabled": move.get("affordable", True),
        "tooltip": move_lines(move, resource_name),
    } for move in moves]
