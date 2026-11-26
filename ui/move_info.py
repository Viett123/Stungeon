"""Turns a move into text lines and a hotbar entry (owner: B).

Used by the hotbar tooltip and by the combat screen, so both always say the same thing.
"""
from core.strings import t
from systems.player import load_data
from ui import slots, theme


def damage_text(move):
    if move["questions"] == 0:
        return t("move_no_question")
    if move["questions"] > 1:
        return t("move_damage_ultimate", damage=move["damage"], n=move["questions"])
    return t("move_damage", damage=move["damage"])


# What a move does besides damage, by move id: the key in core/strings_en.json.
EFFECT_TEXTS = {"war_cry": "utility_war_cry", "reveal": "utility_reveal", "evasion": "utility_evasion",
                "shield_bash": "move_effect_stun", "poison_arrow": "move_effect_poison"}


def effect_text(move_id):
    """"Your next attack deals +50% damage." and so on, or None for a plain attack.
    The numbers come from data/combat.json, so the text is right when they change."""
    key = EFFECT_TEXTS.get(move_id)
    if key is None:
        return None
    numbers = load_data("combat.json")
    utility, effects = numbers["utility"], numbers["move_effects"]
    return t(key,
             bonus=round(utility["war_cry_bonus"] * 100),
             n=utility["reveal_wrong_choices_removed"],
             attacks=utility["evasion_attacks"],
             miss=round(utility["evasion_miss_chance"] * 100),
             stun=round(effects["stun_chance"] * 100),
             poison=effects["poison_damage"], turns=effects["poison_turns"])


def move_lines(move, resource_name):
    """[(text, colour), ...] describing a move: name, tier, damage, what else it does, cost."""
    affordable = move.get("affordable", True)
    lines = [
        (move["name"], theme.GOLD),
        (t(f"tier_{move['tier']}"), theme.TEXT),
        (damage_text(move), theme.TEXT),
    ]
    effect = effect_text(move["id"])
    if effect:
        lines.append((effect, theme.GOOD))
    lines.append((t("move_cost", cost=move["cost"], resource=resource_name), theme.TEXT if affordable else theme.BAD))
    return lines


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
