"""The risk-and-reward choice between two floors (owner: D). No pygame here.

The choices and their numbers are in data/choices.json. This file only offers some
of them and carries out the one the player picks.
"""
from systems import inventory
from systems.player import load_data


def offer(rng) -> list[dict]:
    """A few random choices for the player to pick from. Uses the run's rng."""
    data = load_data("choices.json")
    return rng.sample(data["choices"], min(data["offered"], len(data["choices"])))


def apply(choice, run) -> None:
    """Carry out a choice on the run: its player now, and the next floor later."""
    effects = choice["effects"]
    player = run.player
    player.gold += effects.get("gold", 0)
    if "item" in effects:
        inventory.add_item(player, effects["item"])       # a full bag simply loses it
    if "lose_hp" in effects:
        # A choice may hurt, but it never kills: at least 1 HP is left.
        player.take_damage(min(effects["lose_hp"], player.hp - 1))
    player.max_hp += effects.get("max_hp", 0)
    for name, amount in effects.get("next_floor", {}).items():
        run.next_modifiers[name] = run.next_modifiers.get(name, 0) + amount
